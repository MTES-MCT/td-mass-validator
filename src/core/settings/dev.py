from .base import *  # noqa

DEBUG = True

SECRET_KEY = "xyzabcdefghu"

INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405
