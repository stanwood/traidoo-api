import pytest


@pytest.fixture(autouse=True)
def bucket(bucket):
    bucket.return_value.blob.return_value.download_as_string.return_value = "data"
    bucket.return_value.blob.return_value.content_type = "text/plain"
    yield bucket
