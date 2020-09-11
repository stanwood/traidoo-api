from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.core.validators import EMPTY_VALUES
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from common.admin import BaseRegionalAdminMixin
from settings.models import GlobalSetting, Setting


@admin.register(GlobalSetting)
class GlobalSettingAdmin(ModelAdmin, DynamicArrayMixin):
    list_display = ("id",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if self.model.objects.all().count() == 1:
            obj = self.model.objects.all()[0]
            return HttpResponseRedirect(
                reverse(
                    f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                    args=(obj.id,),
                )
            )
        return super(GlobalSettingAdmin, self).changelist_view(
            request=request, extra_context=extra_context
        )


class SettingAdminForm(ModelForm):
    class Meta:
        model = Setting
        fields = "__all__"

    def clean(self):
        is_central_logistics_company = self.cleaned_data.get(
            "central_logistics_company", False
        )
        if is_central_logistics_company:
            logistics_company = self.cleaned_data.get("logistics_company", None)
            if logistics_company in EMPTY_VALUES:
                self._errors["logistics_company"] = self.error_class(
                    [_("This field is required.")]
                )
        return self.cleaned_data


@admin.register(Setting)
class SettingAdmin(BaseRegionalAdminMixin, ModelAdmin):
    ordering = ("id",)
    form = SettingAdminForm
    list_display = (
        "id",
        "charge",
        "mc_swiss_delivery_fee_vat",
        "platform_fee_vat",
        "transport_insurance",
        "deposit_vat",
        "min_purchase_value",
        "platform_user",
        "central_logistics_company",
        "logistics_company",
    )

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
