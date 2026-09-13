import os
import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load backend_report_moe/.env (see .env.example). OS/Docker env wins by default.
load_dotenv(BASE_DIR / ".env")


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return [part.strip() for part in raw.split(",") if part.strip()]


def _lan_origins() -> list[str]:
    """Trust browsers that open the stack by LAN IP (port 80 + app ports)."""
    hosts = _env_list("LAN_HOSTS", ["192.168.150.51"])
    extra_ports = ("", ":4200", ":4201", ":8001")
    origins: list[str] = []
    for raw in hosts:
        value = raw.strip().rstrip("/")
        if not value:
            continue
        if "://" in value:
            origins.append(value)
            continue
        host = value.split("/")[0]
        if ":" in host:
            origins.append(f"http://{host}")
            continue
        for port in extra_ports:
            origins.append(f"http://{host}{port}")
    return origins


def _unique_origins(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for item in group:
            if item not in seen:
                seen.add(item)
                out.append(item)
    return out


def _discover_geodjango_paths() -> tuple[str | None, str | None, str | None]:
    """Find GDAL/GEOS/PROJ on Windows (QGIS / OSGeo4W) when env vars are unset."""
    if sys.platform != "win32":
        return None, None, None

    candidates = [
        Path(r"C:\Program Files\QGIS 4.0.1"),
        Path(r"C:\OSGeo4W64"),
        Path(r"C:\OSGeo4W"),
    ]
    extra_root = os.environ.get("QGIS_ROOT", "").strip()
    if extra_root:
        candidates.insert(0, Path(extra_root))

    for root in candidates:
        bin_dir = root / "bin"
        if not bin_dir.is_dir():
            continue
        gdal_dlls = sorted(bin_dir.glob("gdal3*.dll"), reverse=True)
        if not gdal_dlls:
            gdal_dlls = sorted(bin_dir.glob("gdal*.dll"), reverse=True)
        geos_dll = bin_dir / "geos_c.dll"
        proj_share = root / "share" / "proj"
        if gdal_dlls and geos_dll.is_file():
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(bin_dir))
            return (
                str(gdal_dlls[0]),
                str(geos_dll),
                str(proj_share) if proj_share.is_dir() else None,
            )
    return None, None, None


_auto_gdal, _auto_geos, _auto_proj = _discover_geodjango_paths()

if os.environ.get("GDAL_LIBRARY_PATH"):
    GDAL_LIBRARY_PATH = os.environ["GDAL_LIBRARY_PATH"]
elif _auto_gdal:
    GDAL_LIBRARY_PATH = _auto_gdal

if os.environ.get("GEOS_LIBRARY_PATH"):
    GEOS_LIBRARY_PATH = os.environ["GEOS_LIBRARY_PATH"]
elif _auto_geos:
    GEOS_LIBRARY_PATH = _auto_geos

if os.environ.get("PROJ_LIB"):
    os.environ["PROJ_LIB"] = os.environ["PROJ_LIB"]
elif _auto_proj:
    os.environ.setdefault("PROJ_LIB", _auto_proj)

# GeoDjango on Windows with a standalone GDAL build (DLLs alongside an
# unversioned gdal.dll, e.g. C:\Program Files\GDAL). Django can't autodetect it,
# so GDAL_LIBRARY_PATH/GEOS_LIBRARY_PATH are set explicitly (see .env). We then:
#   1. Add the DLL folder to the search path so dependencies resolve, and
#   2. Point PROJ_LIB/GDAL_DATA at that build's own data (otherwise a different
#      GDAL/PROJ on the machine, e.g. PostgreSQL's, is used at runtime), and
#   3. Preload gdal.dll *now* — before app models (and libs like psycopg/lxml)
#      import — so its bundled deps (proj, sqlite, crypto, xml2, ...) bind to the
#      sibling DLLs instead of a mismatched copy that yields "WinError 127".
if sys.platform == "win32":
    _gdal_lib = globals().get("GDAL_LIBRARY_PATH")
    _geos_lib = globals().get("GEOS_LIBRARY_PATH")

    if hasattr(os, "add_dll_directory"):
        for _dll_path in (_gdal_lib, _geos_lib):
            if not _dll_path:
                continue
            _dll_dir = os.path.dirname(_dll_path)
            if os.path.isdir(_dll_dir):
                try:
                    os.add_dll_directory(_dll_dir)
                except OSError:
                    pass

    if _gdal_lib and os.path.isfile(_gdal_lib):
        _gdal_root = os.path.dirname(_gdal_lib)
        _proj_dir = os.path.join(_gdal_root, "projlib")
        _gdal_data_dir = os.path.join(_gdal_root, "gdal-data")
        if os.path.isdir(_proj_dir):
            os.environ["PROJ_LIB"] = _proj_dir
        if os.path.isdir(_gdal_data_dir):
            os.environ["GDAL_DATA"] = _gdal_data_dir

        import ctypes

        try:
            ctypes.CDLL(_gdal_lib)
        except OSError:
            pass


SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-default-key-for-dev")

DEBUG = os.environ.get("DEBUG", "1") == "1"

ALLOWED_HOSTS = _env_list(
    "ALLOWED_HOSTS",
    ["*"] if DEBUG else ["localhost", "127.0.0.1"],
)

INSTALLED_APPS = [
    "runserver_port.apps.RunserverPortConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "corsheaders",
    "accounts.apps.AccountsConfig",
    "dynamic_forms.apps.DynamicFormsConfig",
    "project_budget.apps.ProjectBudgetConfig",
    "locations.apps.LocationsConfig",
    "master_data.apps.MasterDataConfig",
    # ── من moeds: تطبيقات القطاعات والبوابة ──────────────────────────────────
    "map_layers",
    "oil_gas",
    "electricity",
    "projects",
    "datasets",
    "water",
    "geology",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_USE_POSTGIS = bool(os.environ.get("DB_HOST"))

if _USE_POSTGIS:
    # One connection sees both schemas. Before the merge each project had its own
    # alias plus a router so it could read the other's tables through unmanaged
    # mirror models; with a single backend that whole layer is gone and every
    # table is reachable by plain ORM.
    _search_path = os.environ.get("DB_SEARCH_PATH", "report_moe,moeds,public")
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": os.environ.get("DB_NAME", "moe_shared"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("DB_HOST", "db"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "OPTIONS": {"options": f"-c search_path={_search_path}"},
            # Persistent connections: the default (0) opened a fresh TCP+auth
            # handshake for every request, on top of the two queries session +
            # auth middleware already cost. CONN_HEALTH_CHECKS keeps a recycled
            # connection from being handed out dead after a database restart.
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
            "CONN_HEALTH_CHECKS": True,
            # Every request is one transaction: a view that writes a user row,
            # then its sub-section, title-category and title assignments either
            # lands whole or not at all. Without this, Django's autocommit makes
            # each statement its own transaction and a mid-view failure leaves a
            # half-written record behind. Views that stream or hold the request
            # open for a long export are excluded with @non_atomic_requests.
            "ATOMIC_REQUESTS": True,
        },
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "ATOMIC_REQUESTS": True,
        }
    }

# Default CSV directory for import_locations (override in .env).
LOCATIONS_DATA_DIR = os.environ.get(
    "LOCATIONS_DATA_DIR",
    str(BASE_DIR.parent / "docs" / "locations"),
)

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# report_moe signs its own sessions. The old MOE_AUTH_SECRET override made this
# key identical to moeds' so session cookies were interchangeable between the two
# projects; that shared signing key was the last thing keeping the logins joined.

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", _("English")),
    ("ar", _("Arabic")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# collectstatic target for production (nginx serves this directly) — must differ
# from STATICFILES_DIRS above, which is a source dir.
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Django REST Framework ─────────────────────────────────────────────────────

# Django sessions are the single authentication mechanism for every client (both
# Angular SPAs). The portal used to authenticate with JWT while this side used
# sessions; running both in one backend meant two ways to identify a caller, two
# revocation stories and two sets of failure modes. Sessions won because they were
# already the mechanism here, and a session can actually be revoked server-side —
# a stateless token cannot. CSRF is enforced (SessionAuthentication.enforce_csrf);
# there is no /api/ exemption. CsrfSessionAuthentication only adds a 401 (not 403)
# response for anonymous callers so the SPA interceptors can redirect to /login.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "dynamic_forms.authentication.CsrfSessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Sector report downloads use ?format=xlsx|pdf as a file-type switch.
    # DRF's default URL_FORMAT_OVERRIDE='format' treats that as a renderer
    # name and 404s because there is no xlsx/pdf renderer.
    "URL_FORMAT_OVERRIDE": None,
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/min",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── Session & CSRF cookies ───────────────────────────────────────────────────
#
# Every client authenticates with the Django session cookie. CSRF is enforced on
# unsafe methods (SessionAuthentication.enforce_csrf); the login POST carries no
# session yet so it is not checked, and django.contrib.auth.login() rotates the
# csrftoken cookie on success. The SPAs read that cookie and echo it as
# X-CSRFToken (Angular's built-in XSRF, configured with Django's names).
#
# In production every frontend is served same-origin behind one nginx, so
# SameSite=Lax is sufficient and CORS is unused. Set *_SECURE=1 (the non-DEBUG
# default) whenever the site is served over HTTPS.

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # the SPA must read this cookie to echo the header

SESSION_COOKIE_SECURE = os.environ.get(
    "SESSION_COOKIE_SECURE", "0" if DEBUG else "1") == "1"
CSRF_COOKIE_SECURE = os.environ.get(
    "CSRF_COOKIE_SECURE", "0" if DEBUG else "1") == "1"

# nginx terminates TLS and forwards X-Forwarded-Proto; without this Django thinks
# every proxied request is plain HTTP (breaks Secure cookies and CSRF origin
# checks behind the proxy).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Optional production hardening, opt-in via env (leave unset in dev / behind a
# TLS-terminating proxy that already redirects).
if os.environ.get("SECURE_SSL_REDIRECT") == "1":
    SECURE_SSL_REDIRECT = True
_hsts = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
if _hsts:
    SECURE_HSTS_SECONDS = _hsts
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
_session_age = os.environ.get("SESSION_COOKIE_AGE")
if _session_age:
    SESSION_COOKIE_AGE = int(_session_age)

# ── CORS ──────────────────────────────────────────────────────────────────────
#
# Only needed when a browser client is cross-origin (dev: ng serve without a
# proxy, or a deployment that splits frontend/API hosts). The recommended
# single-origin production topology leaves this empty.

_DEFAULT_FRONTEND_ORIGINS = [
    "http://localhost:4001",
    "http://127.0.0.1:4001",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:4201",
    "http://127.0.0.1:4201",
    "http://localhost:4202",
    "http://127.0.0.1:4202",
]

CORS_ALLOWED_ORIGINS = _unique_origins(
    _env_list("CORS_ALLOWED_ORIGINS", _DEFAULT_FRONTEND_ORIGINS),
    _lan_origins(),
)
CORS_ALLOW_CREDENTIALS = True

# Django 4+ requires the scheme; production must supply https:// origins via env.
CSRF_TRUSTED_ORIGINS = _unique_origins(
    _env_list("CSRF_TRUSTED_ORIGINS", _DEFAULT_FRONTEND_ORIGINS),
    _lan_origins(),
)

# ── Uploaded form files (URLs stored in Info.value) ──────────────────────────
# Default max size 2 MiB. Override with MAX_UPLOAD_SIZE_BYTES or MAX_UPLOAD_SIZE_MB (float).
_MAX_UPLOAD_MB = float(os.environ.get("MAX_UPLOAD_SIZE_MB", "2"))
MAX_UPLOAD_SIZE_BYTES = int(
    os.environ.get(
        "MAX_UPLOAD_SIZE_BYTES",
        str(int(_MAX_UPLOAD_MB * 1024 * 1024)),
    )
)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Export reports (Excel / Word / PDF) ──────────────────────────────────────
# Max confirmed Info rows per file download. Override with EXPORT_MAX_ROWS.
EXPORT_MAX_ROWS = int(os.environ.get("EXPORT_MAX_ROWS", "50000"))
