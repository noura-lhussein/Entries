from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings

# PostGIS catalog — restored automatically on the target when PostGIS is enabled.
SYSTEM_TABLES = ('spatial_ref_sys',)

# Migration history belongs to each server — never export or truncate it.
SCHEMA_META_TABLES = ('django_migrations',)

# Sessions and JWT blacklist are environment-specific; skip by default.
EPHEMERAL_TABLES = (
    'django_session',
    'token_blacklist_blacklistedtoken',
    'token_blacklist_outstandingtoken',
    'django_admin_log',
)

DEFAULT_EXPORT_DIR = Path(settings.BASE_DIR) / 'exports'


@dataclass(frozen=True)
class DbConfig:
    name: str
    user: str
    password: str
    host: str
    port: str


@dataclass(frozen=True)
class ExportManifest:
    created_at: str
    database: str
    host: str
    data_only: bool
    exclude_ephemeral: bool
    include_media: bool
    dump_file: str
    media_archive: str | None
    table_counts: dict[str, int]


def db_config() -> DbConfig:
    db = settings.DATABASES['default']
    return DbConfig(
        name=db['NAME'],
        user=db['USER'],
        password=db['PASSWORD'],
        host=db.get('HOST') or '127.0.0.1',
        port=str(db.get('PORT') or '5432'),
    )


def find_pg_tool(tool_name: str) -> str:
    found = shutil.which(tool_name)
    if found:
        return found
    for candidate in (
        f'/opt/homebrew/opt/postgresql@16/bin/{tool_name}',
        f'/usr/local/opt/postgresql@16/bin/{tool_name}',
        f'/opt/homebrew/opt/postgresql/bin/{tool_name}',
        f'/usr/local/opt/postgresql/bin/{tool_name}',
    ):
        if Path(candidate).is_file():
            return candidate
    raise FileNotFoundError(
        f'{tool_name} not found in PATH. Install PostgreSQL client tools '
        f'(e.g. brew install postgresql@16) or add the bin directory to PATH.'
    )


def _pg_env(config: DbConfig) -> dict[str, str]:
    env = os.environ.copy()
    env['PGPASSWORD'] = config.password
    return env


def list_public_tables() -> list[str]:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        return [row[0] for row in cursor.fetchall()]


def table_row_counts(tables: list[str] | None = None) -> dict[str, int]:
    from django.db import connection

    names = tables or list_public_tables()
    counts: dict[str, int] = {}
    with connection.cursor() as cursor:
        for table in names:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            counts[table] = cursor.fetchone()[0]
    return counts


def tables_to_clear(*, keep_migrations: bool = True) -> list[str]:
    skip = set(SYSTEM_TABLES)
    if keep_migrations:
        skip.update(SCHEMA_META_TABLES)
    return [table for table in list_public_tables() if table not in skip]


def cross_schema_cascade_targets(tables: list[str]) -> list[tuple[str, str]]:
    """Tables outside `public` that TRUNCATE ... CASCADE would also empty.

    `moe_shared` holds moeds in schema `moeds` and report_moe in `report_moe`. CASCADE
    follows foreign keys regardless of schema, so a truncate aimed at `public` can reach
    into either. Returns (schema, table) pairs that reference the truncate set.
    """
    from django.db import connection

    if not tables:
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT src_ns.nspname, src.relname
            FROM pg_constraint c
            JOIN pg_class src ON src.oid = c.conrelid
            JOIN pg_namespace src_ns ON src_ns.oid = src.relnamespace
            JOIN pg_class tgt ON tgt.oid = c.confrelid
            JOIN pg_namespace tgt_ns ON tgt_ns.oid = tgt.relnamespace
            WHERE c.contype = 'f'
              AND tgt_ns.nspname = 'public'
              AND tgt.relname = ANY(%s)
              AND src_ns.nspname <> 'public'
            ORDER BY 1, 2
            """,
            [tables],
        )
        return [(row[0], row[1]) for row in cursor.fetchall()]


def clear_portal_data(*, keep_migrations: bool = True, force: bool = False) -> list[str]:
    """Delete all rows from application tables while keeping the schema.

    Refuses to run outside DEBUG, and refuses when CASCADE would reach another schema,
    unless `force=True`.
    """
    from django.db import connection

    tables = tables_to_clear(keep_migrations=keep_migrations)
    if not tables:
        return tables

    if not force:
        if not settings.DEBUG:
            raise RuntimeError(
                'clear_portal_data truncates every public-schema table and is blocked '
                'when DJANGO_DEBUG=False. Pass force=True only if you are certain.'
            )
        spill = cross_schema_cascade_targets(tables)
        if spill:
            listed = ', '.join(f'{schema}.{table}' for schema, table in spill)
            raise RuntimeError(
                'TRUNCATE ... CASCADE would also empty tables outside `public`, '
                f'including data owned by the sibling project: {listed}. '
                'Refusing. Pass force=True to override.'
            )

    quoted = ', '.join(f'"{table}"' for table in tables)
    with connection.cursor() as cursor:
        cursor.execute(f'TRUNCATE {quoted} RESTART IDENTITY CASCADE')
    return tables


def clear_media() -> None:
    media_root = Path(settings.MEDIA_ROOT)
    if not media_root.is_dir():
        return
    for child in media_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def export_bundle_path(base_dir: Path | None = None) -> Path:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    root = base_dir or DEFAULT_EXPORT_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root / f'moe_portal_{stamp}'


def run_pg_dump(
    output_file: Path,
    *,
    data_only: bool = False,
    exclude_ephemeral: bool = True,
) -> None:
    config = db_config()
    pg_dump = find_pg_tool('pg_dump')
    cmd = [
        pg_dump,
        '--format=custom',
        '--no-owner',
        '--no-acl',
        '--verbose',
        '--schema=public',
        '--file',
        str(output_file),
        '--host',
        config.host,
        '--port',
        config.port,
        '--username',
        config.user,
        config.name,
    ]
    if data_only:
        cmd.append('--data-only')
    for table in SYSTEM_TABLES:
        cmd.extend(['--exclude-table', table])
    for table in SCHEMA_META_TABLES:
        cmd.extend(['--exclude-table', table])
    if exclude_ephemeral:
        for table in EPHEMERAL_TABLES:
            cmd.extend(['--exclude-table', table])

    subprocess.run(cmd, check=True, env=_pg_env(config))


def run_pg_restore(
    dump_file: Path,
    *,
    data_only: bool = False,
    clean: bool = False,
    jobs: int = 4,
) -> None:
    config = db_config()
    pg_restore = find_pg_tool('pg_restore')
    cmd = [
        pg_restore,
        '--verbose',
        '--no-owner',
        '--no-acl',
        '--host',
        config.host,
        '--port',
        config.port,
        '--username',
        config.user,
        '--dbname',
        config.name,
        '--jobs',
        str(max(1, jobs)),
    ]
    if data_only:
        cmd.extend(['--data-only', '--disable-triggers'])
    if clean:
        cmd.append('--clean')
    cmd.append(str(dump_file))
    subprocess.run(cmd, check=True, env=_pg_env(config))


def archive_media(output_file: Path) -> bool:
    media_root = Path(settings.MEDIA_ROOT)
    if not media_root.is_dir() or not any(media_root.iterdir()):
        return False
    with tarfile.open(output_file, 'w:gz') as archive:
        archive.add(media_root, arcname='media')
    return True


def extract_media(archive_file: Path, *, replace: bool = True) -> None:
    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_file, 'r:gz') as archive:
        members = [member for member in archive.getmembers() if member.name.startswith('media/')]
        if replace:
            for member in members:
                target = media_root / Path(member.name).relative_to('media')
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif target.exists():
                    target.unlink()
        archive.extractall(path=settings.BASE_DIR, members=members)


def export_portal_data(
    output_dir: Path | None = None,
    *,
    data_only: bool = False,
    exclude_ephemeral: bool = True,
    include_media: bool = False,
) -> Path:
    bundle_dir = output_dir or export_bundle_path()
    bundle_dir.mkdir(parents=True, exist_ok=True)
    dump_file = bundle_dir / 'database.dump'
    counts = table_row_counts()

    run_pg_dump(
        dump_file,
        data_only=data_only,
        exclude_ephemeral=exclude_ephemeral,
    )

    media_archive: Path | None = None
    if include_media:
        media_archive = bundle_dir / 'media.tar.gz'
        if not archive_media(media_archive):
            media_archive.unlink(missing_ok=True)
            media_archive = None

    config = db_config()
    manifest = ExportManifest(
        created_at=datetime.now(timezone.utc).isoformat(),
        database=config.name,
        host=config.host,
        data_only=data_only,
        exclude_ephemeral=exclude_ephemeral,
        include_media=include_media and media_archive is not None,
        dump_file=dump_file.name,
        media_archive=media_archive.name if media_archive else None,
        table_counts=counts,
    )
    (bundle_dir / 'manifest.json').write_text(
        json.dumps(asdict(manifest), indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    return bundle_dir


def import_portal_data(
    bundle_dir: Path,
    *,
    data_only: bool = False,
    clean: bool = False,
    replace: bool = False,
    include_media: bool = True,
    jobs: int = 4,
) -> ExportManifest:
    manifest_path = bundle_dir / 'manifest.json'
    if not manifest_path.is_file():
        raise FileNotFoundError(f'Missing manifest.json in {bundle_dir}')

    manifest_data = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest = ExportManifest(**manifest_data)
    dump_file = bundle_dir / manifest.dump_file
    if not dump_file.is_file():
        raise FileNotFoundError(f'Missing dump file: {dump_file}')

    if replace:
        clear_portal_data()
        if include_media and manifest.media_archive:
            clear_media()
        restore_data_only = True
        restore_clean = False
        restore_jobs = 1
    else:
        restore_data_only = data_only or manifest.data_only
        restore_clean = clean
        restore_jobs = jobs

    run_pg_restore(
        dump_file,
        data_only=restore_data_only,
        clean=restore_clean,
        jobs=restore_jobs,
    )

    if include_media and manifest.media_archive:
        media_archive = bundle_dir / manifest.media_archive
        if media_archive.is_file():
            extract_media(media_archive)

    return manifest
