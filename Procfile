# Run web app
web: gunicorn --chdir src core.wsgi:application --log-file -

postdeploy: echo "TD_COMPANY_ELASTICSEARCH_CACERTS_CONTENT" > certs.pem

# Run celery worker
worker: celery --workdir src -A core worker -l info
