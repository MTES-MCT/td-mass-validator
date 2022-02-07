# Run web app
web: gunicorn --chdir src core.wsgi:application --log-file -
# Run celery worker
worker: cd src && celery -A core worker -l info
