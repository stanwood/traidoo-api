#/bin/bash
set -e

gsutil -m cp -r static/* gs://$STATIC_BUCKET/

gcloud app deploy --version 1 --quiet queue.yaml
gcloud app deploy --version 1 --quiet app.yaml
gcloud app deploy --version 1 --quiet cron.yaml
