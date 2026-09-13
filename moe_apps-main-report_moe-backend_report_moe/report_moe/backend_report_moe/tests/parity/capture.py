"""Capture and compare API responses across the Ninja -> DRF conversion.

The portal consumes these responses directly, so a silent change of shape is the
one failure mode no unit test would catch. This records what Ninja returns, and
replays the same calls against DRF to prove they still match.

    # before touching an app, against the still-running Ninja backend
    python tests/parity/capture.py record --base http://localhost:8002 --app water

    # after converting it, against the unified backend
    python tests/parity/capture.py verify --base http://localhost:8001 --app water

Only GET routes are captured: they are the read paths the dashboards depend on,
and replaying writes against a live database is not something a check should do.
"""

from __future__ import annotations

import argparse
import hashlib
import io as _io
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree

BASE_DIR = Path(__file__).resolve().parent
EXCEPTIONS_PATH = BASE_DIR / "exceptions.json"
SCHEMA_PATH = "/api/v1/schema/"
TIMEOUT = 30


def _get(url: str, auth: str | None) -> tuple[int, object]:
    """`auth` is a raw header value: a session cookie here, a bearer token on the
    Ninja side. Both sides are read the same way so one baseline serves both."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    if auth:
        name, _, value = auth.partition(":")
        req.add_header(name.strip(), value.strip())
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            blob = resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        blob = exc.read()
        status = exc.code
    except Exception as exc:  # noqa: BLE001 — a dead endpoint is a finding, not a crash
        return 0, {"__error__": f"{type(exc).__name__}: {exc}"}

    try:
        raw = blob.decode("utf-8")
    except UnicodeDecodeError:
        return status, _describe_binary(blob)
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, {"__raw__": raw[:2000]}


def _describe_binary(blob: bytes) -> dict:
    """Reduce a binary body to something that can be compared meaningfully.

    For .xlsx this must not be a digest of the bytes. openpyxl writes the same
    workbook differently depending on whether lxml is installed — tag spacing and
    where namespaces are declared change, so the digest moves while every cell
    stays the same. Comparing the canonicalised XML of the data parts ignores that
    and still catches a real change in content.

    Anything else keeps size + digest, which is all that can be said about it.
    """
    if blob[:2] != b"PK":
        return {"__binary__": {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}}
    try:
        with zipfile.ZipFile(_io.BytesIO(blob)) as zf:
            names = sorted(zf.namelist())
            # Data lives in the sheets and the shared string table; styles, theme
            # and docProps carry no report content.
            parts = {}
            for name in names:
                if name.startswith("xl/worksheets/") or name == "xl/sharedStrings.xml":
                    parts[name] = ElementTree.canonicalize(
                        zf.read(name).decode("utf-8"), strip_text=True
                    )
        return {"__xlsx__": {"members": names, "parts": parts}}
    except Exception:  # noqa: BLE001 — not a readable workbook; fall back to bytes
        return {"__binary__": {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}}


def _routes(base: str, auth: str | None, app: str | None) -> list[str]:
    """GET routes without path parameters, optionally filtered to one app."""
    status, spec = _get(base.rstrip("/") + SCHEMA_PATH, auth)
    if status != 200 or not isinstance(spec, dict):
        sys.exit(f"cannot read OpenAPI schema from {base}: HTTP {status}")
    out = []
    for path, ops in sorted(spec.get("paths", {}).items()):
        if "get" not in ops or "{" in path:
            continue
        if app and f"/{app}/" not in path:
            continue
        out.append(path)
    return out


# Absolute URLs are built with request.build_absolute_uri, so they carry whichever
# host served the call. The baseline was recorded from the old backend on :8002 and
# is replayed against the new one on :8001 — same payload, different origin. In
# production both are one host, so the origin is folded away rather than reported.
_ORIGIN_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?")


def _normalise(value):
    """Fold representations that differ in spelling but not in meaning.

    Two foldings, both provably invisible to a client:
      * UTC spelled `+00:00` (Ninja) or `Z` (DRF) — same instant, and every JSON
        date parser accepts either.
      * The origin of absolute URLs — an artefact of the two backends listening on
        different ports while the comparison runs.

    Nothing else is folded: a difference a client could observe must still fail.
    """
    if isinstance(value, str):
        value = _ORIGIN_RE.sub("http://HOST", value)
        return value[:-6] + "Z" if value.endswith("+00:00") else value
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalise(v) for k, v in value.items()}
    return value


def _canonical(body) -> str:
    return json.dumps(_normalise(body), sort_keys=True, ensure_ascii=False)


def _exceptions() -> dict:
    if not EXCEPTIONS_PATH.exists():
        return {}
    data = json.loads(EXCEPTIONS_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _is_superset(new, base) -> bool:
    """Every key of the baseline present with an equal value; extras allowed."""
    new, base = _normalise(new), _normalise(base)
    if isinstance(base, dict) and isinstance(new, dict):
        return all(
            k in new and _canonical(new[k]) == _canonical(v) for k, v in base.items()
        )
    return _canonical(new) == _canonical(base)


def _slug(path: str) -> str:
    return path.strip("/").replace("/", "__") or "root"


def _dir(app: str | None) -> Path:
    return BASE_DIR / (app or "_all")


def record(base: str, auth: str | None, app: str | None) -> int:
    routes = _routes(base, auth, app)
    out_dir = _dir(app)
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in routes:
        status, body = _get(base.rstrip("/") + path, auth)
        payload = {"path": path, "status": status, "body": body}
        (out_dir / f"{_slug(path)}.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        print(f"  recorded {status} {path}")
    print(f"\n{len(routes)} route(s) -> {out_dir}")
    return 0


def verify(base: str, auth: str | None, app: str | None) -> int:
    out_dir = _dir(app)
    files = sorted(out_dir.glob("*.json"))
    if not files:
        sys.exit(f"no baseline in {out_dir} — run `record` first")
    allowed = _exceptions()
    mismatches = []
    for f in files:
        expected = json.loads(f.read_text(encoding="utf-8"))
        status, body = _get(base.rstrip("/") + expected["path"], auth)
        rule = allowed.get(expected["path"])
        # sort_keys makes key order irrelevant; everything else must match exactly.
        if rule and rule.get("mode") == "superset":
            same = status == expected["status"] and _is_superset(body, expected["body"])
            label = "ok*"
        else:
            same = status == expected["status"] and _canonical(body) == _canonical(
                expected["body"]
            )
            label = "ok "
        if same:
            print(f"  {label}  {expected['path']}")
        else:
            mismatches.append((expected["path"], expected["status"], status))
            print(f"  DIFF {expected['path']}  ({expected['status']} -> {status})")
    print(f"\n{len(files) - len(mismatches)}/{len(files)} match")
    if mismatches:
        print("\nmismatched:")
        for path, want, got in mismatches:
            print(f"  {path}  expected HTTP {want}, got {got}")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["record", "verify"])
    ap.add_argument("--base", required=True, help="e.g. http://localhost:8002")
    ap.add_argument("--app", help="restrict to one app, e.g. water")
    ap.add_argument(
        "--auth",
        help="raw auth header, e.g. 'Cookie: sessionid=...' or 'Authorization: Bearer ...'",
    )
    args = ap.parse_args()
    return (record if args.mode == "record" else verify)(args.base, args.auth, args.app)


if __name__ == "__main__":
    raise SystemExit(main())
