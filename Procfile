# Run web app
web: gunicorn --chdir src core.wsgi:application --log-file -
# Run celery worker
worker: celery -A core worker -l info
