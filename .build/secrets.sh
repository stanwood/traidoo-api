#/bin/bash
set -e


mkdir -p /workspace/.build/secrets

secrets=("DISTANCE_MATRIX_API_KEY" "MAILGUN_API_KEY" "MANGOPAY_PASSWORD" "POSTGRESQL_PASSWORD" "SECRET_KEY")
for secret in ${secrets[@]}; do
    gcloud secrets versions access latest --secret=$secret > /workspace/.build/secrets/$secret.txt
done

gcloud secrets versions access latest --secret="SERVICE_ACCOUNT" > /workspace/service_account.json
