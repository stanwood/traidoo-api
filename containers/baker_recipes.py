from faker import Faker
from model_bakery.recipe import Recipe, seq

from .models import Container

fake = Faker()


container = Recipe(
    Container,
    size_class=seq(fake.word(ext_word_list=None)),
    standard=fake.pybool(),
    volume=fake.pyfloat(
        left_digits=None, right_digits=None, positive=False, min_value=1, max_value=200
    ),
    deposit=fake.pydecimal(
        left_digits=None, right_digits=None, positive=False, min_value=1, max_value=100
    ),
    delivery_fee=fake.pydecimal(
        left_digits=None, right_digits=None, positive=False, min_value=1, max_value=50
    ),
    image_url=fake.image_url(width=None, height=None),
)
