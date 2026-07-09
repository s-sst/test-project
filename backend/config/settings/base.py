"""
Base Django settings shared across all environments.

Environment-specific overrides live in ``dev.py`` / ``prod.py`` / ``test.py``.
Every environment-sensitive or secret value is read from the process
environment (optionally seeded from a local ``.env`` file). No secrets are
ever committed to source control.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# BASE_DIR -> the ``backend/`` directory (two parents up from this file).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env if present (never fails if missing).
load_dotenv(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
# Small, dependency-free env helpers
# ---------------------------------------------------------------------------
def env_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def env_list(key: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(key)
    if not raw:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Core security
# ---------------------------------------------------------------------------
SECRET_KEY = env_str("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
]

# Local domain modules. Order matters only insofar as the custom user model
# (users) must be installed before anything that references AUTH_USER_MODEL.
LOCAL_APPS = [
    "common",
    "users",
    "authentication",
    "audit_logs",
    "documents",
    "frameworks",
    "assessments",
    "scoring",
    "recommendations",
    "reports",
    "dashboard",
    "ingestion",
    "rag",
    "prompts",
    "api",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom user model — must be set before the first migration is created.
AUTH_USER_MODEL = "users.User"


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Establishes a per-request correlation id + captures the acting user so the
    # audit subsystem can attribute every mutation. Must run after auth.
    "audit_logs.middleware.RequestContextMiddleware",
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
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def _database_from_url(url: str) -> dict:
    """Parse a DATABASE_URL into a Django DATABASES entry.

    Kept dependency-free (no dj-database-url) to honour the "lightweight
    foundation" principle. Supports sqlite and postgres URLs.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.split("+")[0]
    if scheme in {"postgres", "postgresql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
            "CONN_MAX_AGE": 60,
        }
    if scheme == "sqlite":
        name = parsed.path or "/db.sqlite3"
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": name}
    raise ValueError(f"Unsupported DATABASE_URL scheme: {scheme!r}")


_database_url = env_str("DATABASE_URL")
if _database_url:
    DATABASES = {"default": _database_from_url(_database_url)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    # Phase 1 foundation ships permissive so the platform is demoable without
    # an auth dance. Fine-grained RBAC is a later phase (see users.roles).
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # Rule 3: JSON responses only. No Browsable API / markdown in base.
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "EXCEPTION_HANDLER": "common.exceptions.governed_exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env_str("THROTTLE_ANON", "120/min"),
        "user": env_str("THROTTLE_USER", "1000/min"),
    },
}

# ---------------------------------------------------------------------------
# Security / RBAC (Phase 8)
# ---------------------------------------------------------------------------
# When RBAC enforcement is off (dev/demo default) all endpoints remain open so
# the platform is trivially demoable. Production enables it (see prod.py), and
# write/override endpoints then require an authenticated user with a sufficient
# role. Reads stay open unless you also tighten DEFAULT_PERMISSION_CLASSES.
SECURITY = {
    "ENFORCE_RBAC": env_bool("ENFORCE_RBAC", False),
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", ["http://localhost:5173", "http://localhost:3000"]
)
CORS_ALLOW_CREDENTIALS = True


# ---------------------------------------------------------------------------
# Platform-specific configuration (namespaced under GOVERNANCE)
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = env_int("MAX_UPLOAD_SIZE_MB", 50)
ALLOWED_UPLOAD_EXTENSIONS = env_list(
    "ALLOWED_UPLOAD_EXTENSIONS", ["pdf", "docx", "png", "jpg", "jpeg", "tiff"]
)
FRAMEWORKS_DATA_DIR = BASE_DIR / env_str("FRAMEWORKS_DATA_DIR", "frameworks_data")

GOVERNANCE = {
    "MAX_UPLOAD_SIZE_BYTES": MAX_UPLOAD_SIZE_MB * 1024 * 1024,
    "ALLOWED_UPLOAD_EXTENSIONS": ALLOWED_UPLOAD_EXTENSIONS,
    # Extension -> allowed MIME types (defence-in-depth: extension + sniffed MIME).
    "ALLOWED_MIME_TYPES": {
        "pdf": ["application/pdf"],
        "docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/zip",  # DOCX is a zip container; some sniffers report zip.
        ],
        "png": ["image/png"],
        "jpg": ["image/jpeg"],
        "jpeg": ["image/jpeg"],
        "tiff": ["image/tiff"],
    },
    "FRAMEWORKS_DATA_DIR": FRAMEWORKS_DATA_DIR,
}

# ---------------------------------------------------------------------------
# RAG configuration (Phase 3). Lightweight + pluggable: the defaults are
# dependency-free (deterministic hashing embedder + DB-backed vector index) so
# the platform runs and tests reproducibly anywhere. Set EMBEDDING_BACKEND=
# sentence_transformers and VECTOR_INDEX=chroma to opt into the heavy stack.
# ---------------------------------------------------------------------------
RAG = {
    "EMBEDDING_BACKEND": env_str("EMBEDDING_BACKEND", "hashing"),  # hashing | sentence_transformers
    "EMBEDDING_MODEL": env_str("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
    "EMBEDDING_DIM": env_int("EMBEDDING_DIM", 256),
    "VECTOR_INDEX": env_str("VECTOR_INDEX", "db"),  # db | chroma
    "CHUNK_SIZE": env_int("RAG_CHUNK_SIZE", 900),
    "CHUNK_OVERLAP": env_int("RAG_CHUNK_OVERLAP", 150),
    "RETRIEVAL_TOP_K": env_int("RAG_TOP_K", 6),
    "CHROMA_PERSIST_DIR": env_str("CHROMA_PERSIST_DIR", str(BASE_DIR / ".chroma")),
}

# ---------------------------------------------------------------------------
# LLM configuration (Phase 4). Provider-agnostic. Default is a deterministic
# offline mock (no key, fully testable); set LLM_PROVIDER + LLM_API_KEY to use a
# real provider (Anthropic Claude / OpenAI / Gemini / Ollama).
# ---------------------------------------------------------------------------
LLM = {
    "PROVIDER": env_str("LLM_PROVIDER", "mock"),  # mock | anthropic | openai | gemini | ollama
    "MODEL": env_str("LLM_MODEL", "claude-opus-4-8"),
    "API_KEY": env_str("LLM_API_KEY", "") or env_str("ANTHROPIC_API_KEY", ""),
    "BASE_URL": env_str("LLM_BASE_URL", ""),
    "TEMPERATURE": float(env_str("LLM_TEMPERATURE", "0.0")),
    "MAX_TOKENS": env_int("LLM_MAX_TOKENS", 1500),
    "SEED": env_int("LLM_SEED", 42),
    "CONFIDENCE_THRESHOLD": float(env_str("LLM_CONFIDENCE_THRESHOLD", "0.55")),
    "MAX_RETRIES": env_int("LLM_MAX_RETRIES", 2),
}
# If an Anthropic key is present but provider left as mock, auto-upgrade to Claude.
if LLM["PROVIDER"] == "mock" and LLM["API_KEY"]:
    LLM["PROVIDER"] = "anthropic"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": env_str("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
