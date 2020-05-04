import pytest
from model_mommy import mommy

from categories.models import Category


@pytest.mark.django_db
def test_cannot_remove_category_assigned_to_product(client_admin):
    category = mommy.make('categories.Category')
    product = mommy.make('products.Product', category=category)
    response = client_admin.delete(f'/categories/{category.id}')

    response.status_code == 400
    response.json() == {
        'message': 'Cannot be deleted due to protected related entities.',
        'code': 'protected_error',
    }


@pytest.mark.django_db
def test_admin_can_delete_category(client_admin):
    category = mommy.make('categories.Category')
    response = client_admin.delete(f'/categories/{category.id}')

    response.status_code == 204
    with pytest.raises(Category.DoesNotExist):
        category.refresh_from_db()
