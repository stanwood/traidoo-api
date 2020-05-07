from copy import copy

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from reversion.admin import VersionAdmin

from common.admin import BaseRegionalAdminMixin
from mails.utils import send_mail
from products.models import Product

User = get_user_model()


class GroupsFilter(admin.SimpleListFilter):
    title = "Groups filter"
    parameter_name = "group_name"

    def lookups(self, request, model_admin):
        return [("inactive", "To approve")] + [
            (group.name, group.name) for group in Group.objects.all()
        ]

    def queryset(self, request, queryset):
        if self.value() == "inactive":
            return queryset.filter(groups__isnull=True)
        elif self.value() is None:
            return queryset
        else:
            return queryset.filter(groups__name=self.value())


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ["date_joined"]
        readonly_fields = ["is_superuser"]


class ProductsInline(BaseRegionalAdminMixin, admin.TabularInline):
    model = Product
    fields = ["name", "region", "regions"]


@admin.register(User)
class UserAdmin(BaseRegionalAdminMixin, VersionAdmin):
    form = UserAdminForm
    fieldsets = (
        (None, {"fields": tuple(User.REQUIRED_FIELDS) + ("email",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_email_verified",
                    "is_cooperative_member",
                    "groups",
                    "is_superuser",
                    "region",
                )
            },
        ),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "company_name",
        "is_staff",
        "is_active",
        "is_email_verified",
        "is_cooperative_member",
        "approval_status",
        "mangopay_user_id",
        "mangopay_validation_level",
        "created_at",
    )
    list_filter = [GroupsFilter, "region"]
    search_fields = ("email", "first_name", "last_name", "company_name")
    ordering = ("-created_at",)

    actions = ["approve_user"]

    inlines = (ProductsInline,)

    def approval_status(self, user) -> bool:
        return bool(user.approved)

    approval_status.boolean = True

    def approve_user(self, request, queryset):
        buyer_group = Group.objects.get(name="buyer")
        seller_group = Group.objects.get(name="seller")
        queryset = queryset.exclude(groups__in=[buyer_group])
        count = 0
        for count, user in enumerate(queryset, start=1):
            user.groups.add(buyer_group)
            if user.declared_as_seller:
                user.groups.add(seller_group)
            user.save()
            send_mail(
                region=user.region,
                subject="Ihr Account wurde aktiviert.",
                recipient_list=[user.email],
                template="mails/users/user_activated.html",
            )

            if not user.mangopay_user_id:
                user.send_task(
                    f"/users/{user.id}/mangopay/create",
                    queue_name="mangopay-create-account",
                    http_method="POST",
                )

        self.message_user(request, f"{count} users activated")

    approve_user.short_description = "Approve user"

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super(UserAdmin, self).get_readonly_fields(request, obj)
        if not request.user.is_superuser:
             read_only_fields += ('is_superuser', 'region')
        return read_only_fields
