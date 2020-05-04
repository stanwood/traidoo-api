import google.cloud.storage
from django.conf import settings
from retrying import retry


class StorageMixin(object):
    @property
    def storage(self):
        return google.cloud.storage.Client()

    @property
    def bucket(self):
        return self.storage.get_bucket(settings.DEFAULT_BUCKET)

    def _store(self, path, data, content_type='application/pdf'):
        blob = self.bucket.blob(path.encode('utf-8'))
        blob.upload_from_string(data, content_type)

        return blob

    @retry(
        stop_max_attempt_number=3,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000,
    )
    def _upload_file_to_gcs(self, path, raw_data, content_type):
        storage_client = google.cloud.storage.Client()

        bucket = storage_client.get_bucket(settings.DEFAULT_BUCKET)

        gcs_file_path = path.encode('utf-8')
        blob = bucket.blob(gcs_file_path)

        blob.upload_from_string(raw_data, content_type)
        blob.make_public()

        return blob.public_url

    def _fetch(self, path):
        blob = self.bucket.blob(path.encode('utf-8'))
        return blob.download_as_string()

    def get_browse_url(self, path):
        return 'https://console.cloud.google.com/storage/browser/{bucket_name}/{path}'.format(
            bucket_name=self.bucket.name, path=path
        )
