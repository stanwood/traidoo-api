from decimal import Decimal

import pytest


@pytest.mark.django_db
def test_category_icon_migration(migrator):
    old_state = migrator.apply_initial_migration(
        ("categories", "0003_auto_20200520_1539")
    )

    Category = old_state.apps.get_model("categories", "Category")

    category_1 = Category.objects.create(
        name="Test 1", icon="2", ordering=1, default_vat=1.2
    )
    category_2 = Category.objects.create(
        name="Test 2", icon="a", ordering=2, default_vat=1.3, parent=category_1
    )

    with pytest.raises(LookupError):
        # Models does not yet exist:
        old_state.apps.get_model("categories", "CategoryIcon")

    new_state = migrator.apply_tested_migration(
        ("categories", "0010_auto_20200806_1109")
    )

    CategoryIcon = new_state.apps.get_model("categories", "CategoryIcon")
    assert CategoryIcon.objects.count() == 35

    Category = new_state.apps.get_model("categories", "Category")

    category_1 = Category.objects.get(name="Test 1")
    category_2 = Category.objects.get(name="Test 2")

    assert category_1.icon.id == 2
    assert category_2.icon.id == 1

    assert category_1.ordering == 1
    assert category_2.ordering == 2

    assert category_1.default_vat == Decimal("1.2")
    assert category_2.default_vat == Decimal("1.3")

    assert not category_1.parent
    assert category_2.parent == category_1
