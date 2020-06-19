import pytest
from model_bakery import baker

from products.models import Product


@pytest.mark.django_db
def test_admin_can_delete_product(seller, client_admin, traidoo_region):
    product = baker.make('products.Product', seller=seller, region=traidoo_region)

    response = client_admin.delete(f'/products/{product.id}')

    assert response.status_code == 204

    with pytest.raises(Product.DoesNotExist):
        product.refresh_from_db()
