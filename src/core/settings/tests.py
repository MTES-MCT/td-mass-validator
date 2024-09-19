from .base import *  # noqa

DEBUG = True

SECRET_KEY = "abc"

ALLOWED_HOSTS = ["*"]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

TEST_RUNNER = "django.test.runner.DiscoverRunner"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
