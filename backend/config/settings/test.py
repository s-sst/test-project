"""Test settings: fast, isolated, deterministic."""
import tempfile

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK

DEBUG = False

# Disable throttling in tests (avoids cross-test rate-limit flakiness).
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}}

# In-memory SQLite for speed and isolation.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Fast password hashing in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Isolate uploaded-file writes to a throwaway directory.
MEDIA_ROOT = tempfile.mkdtemp(prefix="governance-test-media-")

# Keep test output quiet.
LOGGING = {"version": 1, "disable_existing_loggers": True}
