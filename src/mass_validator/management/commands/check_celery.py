from django.core.management.base import BaseCommand

from core.celery_app import debug_task


class Command(BaseCommand):
    def handle(self, verbosity=0, **kwargs):
        job = debug_task.delay()
        print(job)
