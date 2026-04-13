from .base import *  # noqa: F401, F403

DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]
