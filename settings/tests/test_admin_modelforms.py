from settings.admin import SettingAdminForm


def test_setting_admin_form_logistics_company_required():
    form = SettingAdminForm(data={"central_logistics_company": True})
    assert form.errors["logistics_company"] == ["This field is required."]


def test_setting_admin_form_logistics_company_not_required():
    form = SettingAdminForm(data={"central_logistics_company": False})
    assert not form.errors.get("logistics_company")
