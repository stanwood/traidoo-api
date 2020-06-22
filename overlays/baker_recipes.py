from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker
from model_bakery.recipe import Recipe

from overlays.models import Overlay

fake = Faker()

image_file = SimpleUploadedFile(
    name="test-image.png",
    content=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\nIDATx\x9cc\xfa\x0f\x00\x01\x05\x01\x02\xcf\xa0.\xcd\x00\x00\x00\x00IEND\xaeB`\x82",
    content_type="image/png",
)


overlay = Recipe(
    Overlay,
    title=fake.sentence(),
    subtitle=fake.sentence(),
    body=fake.text(),
    learn_more_url=fake.uri_path(),
    avatar=image_file,
    image=image_file,
)
