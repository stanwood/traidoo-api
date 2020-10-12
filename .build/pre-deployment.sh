#/bin/bash
set -e

wget -O /workspace/cloud_sql_proxy https://storage.googleapis.com/cloudsql-proxy/v1.18.0/cloud_sql_proxy.linux.amd64
chmod +x /workspace/cloud_sql_proxy

/workspace/cloud_sql_proxy -dir=/workspace -instances=$SQL_PROXY_INSTANCE &
PROXY_PID=$!

secrets=("DISTANCE_MATRIX_API_KEY" "MAILGUN_API_KEY" "MANGOPAY_PASSWORD" "POSTGRESQL_PASSWORD" "SECRET_KEY")
for secret in ${secrets[@]}; do
    export $secret=$(cat /workspace/.build/secrets/$secret.txt)
done

pip install -r requirements.txt
pip install pyyaml
apt-get update && apt-get install -y gettext

POSTGRESQL_HOST=localhost python manage.py migrate

kill $PROXY_PID

rm /workspace/cloud_sql_proxy

rm -rf .build/secrets

python .build/render_app_yaml.py

python manage.py collectstatic --noinput
python manage.py compilemessages
