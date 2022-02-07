from .base import *  # noqa

DEBUG = True

SECRET_KEY = "xyzabcdefghu"

INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Celery config
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis"
