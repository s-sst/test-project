"""Production settings: strict security, env-driven, no insecure defaults."""
from .base import *  # noqa: F401,F403
from .base import SECURITY, env_bool, env_str

DEBUG = False

# Enforce role-based access control on write/override endpoints in production
# (overridable via the ENFORCE_RBAC env var).
SECURITY = {**SECURITY, "ENFORCE_RBAC": env_bool("ENFORCE_RBAC", True)}

# Fail fast if the secret key was not overridden.
if SECRET_KEY == "insecure-dev-key-change-me":  # noqa: F405
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set to a strong value in production."
    )

# Security headers / HTTPS hardening.
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

# Serve static files via WhiteNoise if present.
try:  # pragma: no cover - optional dependency
    import whitenoise  # noqa: F401

    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
except ImportError:
    pass
