from .base import *  # noqa
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOST")

ADMINS = [el.split(":") for el in env.list("DJANGO_ADMINS", default=[])]
