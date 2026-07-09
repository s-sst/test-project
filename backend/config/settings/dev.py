"""Development settings: verbose, permissive, SQLite by default."""
from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK, env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)

# Convenient in-browser API exploration during development only. The base
# config stays JSON-only (Rule 3); dev opts into the browsable renderer.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# Relax host checking locally.
ALLOWED_HOSTS = ["*"]
