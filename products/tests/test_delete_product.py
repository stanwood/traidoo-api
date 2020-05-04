import pytest
from model_mommy import mommy

from products.models import Product


@pytest.mark.django_db
def test_admin_can_delete_product(seller, client_admin, traidoo_region):
    product = mommy.make('products.Product', seller=seller, region=traidoo_region)

    response = client_admin.delete(f'/products/{product.id}')

    assert response.status_code == 204

    with pytest.raises(Product.DoesNotExist):
        product.refresh_from_db()
