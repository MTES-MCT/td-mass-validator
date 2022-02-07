import redis
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, verbosity=0, **kwargs):
        redis_url = settings.CELERY_BROKER_URL
        print(redis_url)
        r = redis.Redis.from_url(redis_url)
        print(r)
