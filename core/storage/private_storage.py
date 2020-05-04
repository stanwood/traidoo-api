from django.core.files.storage import DefaultStorage


class GoogleCloudPrivateStorage(DefaultStorage):
    default_acl = "projectPrivate"


private_storage = GoogleCloudPrivateStorage()
