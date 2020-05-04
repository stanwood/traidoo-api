import os
import uuid


def public_logo_upload_to(instance, filename):
    _, filename_ext = os.path.splitext(filename)
    return f"public/{instance._meta.model_name}/{instance.id}/logo{filename_ext}"


def public_image_upload_to(instance, filename):
    _, filename_ext = os.path.splitext(filename)
    return f"public/{instance._meta.model_name}/{instance.id}/{uuid.uuid4().hex}{filename_ext}"


def private_image_upload_to(instance, filename):
    _, filename_ext = os.path.splitext(filename)
    return f"private/{instance._meta.model_name}/{instance.id}/{uuid.uuid4().hex}{filename_ext}"
