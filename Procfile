# Run web app
web: gunicorn --chdir src core.wsgi:application --log-file -

# Run celery worker
worker: celery --workdir src -A core worker -l info
postdeploy: echo "$TD_COMPANY_ELASTICSEARCH_CACERTS_CONTENT" > /app/src/certs.pem