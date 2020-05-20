#!/bin/bash
set -e

pyenv local 3.7
pip install -r requirements.txt
pip install pyyaml python-dotenv
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

echo "Deploying ${PROJECT_ID}"
echo $SERVICE_ACCOUNT > ./service_account.json
gcloud auth activate-service-account --key-file=service_account.json
gcloud config set project $PROJECT_ID

./cloud_sql_proxy -instances=$CLOUD_SQL_INSTANCE=tcp:2345 &
PROXY_PID=$!

python scripts/render_app_yaml.py

python manage.py collectstatic --noinput
gsutil -m cp -r static/* gs://$STATIC_BUCKET/

python manage.py compilemessages

export POSTGRESQL_PORT=2345
export POSTGRESQL_HOST=localhost
python manage.py migrate
kill $PROXY_PID

gcloud app deploy --version 1 --quiet app.yaml
gcloud app deploy --version 1 --quiet queue.yaml
gcloud app deploy --version 1 --quiet cron.yaml
