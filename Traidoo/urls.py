from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from rest_framework.documentation import include_docs_urls
from rest_framework_nested import routers

from carts.views.delete_inactive_carts import DeleteInactiveCartsView
from categories.views import CategoryViewSet
from common.views import RegionViewSet, StaticViewSet
from containers.views import ContainerViewSet
from delivery_addresses.views import DeliveryAddressViewSet
from delivery_options.views import DeliveryOptionViewSet
from documents.views.download import DownloadDocumentAdminView
from groups.views import GroupViewSet
from items.views.items import ItemViewSet, ProductsItemViewSet
from items.views.stats import ItemsStatsView
from jobs.views import JobsViewSet
from orders.views.find_unsold_items import FindUnsoldItemsView
from products.views import ProductViewSet
from routes.tasks.calculate_route_length import CalculateRouteLengthView
from routes.views import RoutesViewSet
from tags.views import TagViewSet
from trucks.views import TruckViewSet
from users.views.delete_not_verified_users import DeleteNotVerifiedUsersView
from users.views.documents import MangopayDocumentsView
from users.views.kyc_documents import UploadUserMangopayKycDocumentView
from users.views.mangopay import CreateMangopayAccountView
from users.views.profile import (
    UserCompanyProfileViewSet,
    UserDocumentsProfileViewSet,
    UserPersonalProfileViewSet,
    UserProfileViewSet,
)
from users.views.registration import RegistrationViewSet

from .warmup import warmup

router = routers.DefaultRouter(trailing_slash=False)

router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"container_types", ContainerViewSet)
router.register(
    r"delivery_addresses", DeliveryAddressViewSet, basename="delivery_address"
)
router.register(r"trucks", TruckViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"jobs", JobsViewSet, basename="jobs")
router.register(r"delivery_options", DeliveryOptionViewSet)
router.register(r"tags", TagViewSet)
router.register(r"routes", RoutesViewSet, basename="routes")
router.register(r"regions", RegionViewSet, basename="regions")
router.register(r"regions/static", StaticViewSet, basename="regions-static")

# Products & Items
router.register(r"products", ProductViewSet, basename="product")
router.register(r"items", ItemViewSet, basename="item")
product_items_router = routers.NestedSimpleRouter(router, r"products", lookup="product")
product_items_router.register(r"items", ProductsItemViewSet, basename="item")

# Admin site translations
admin.site.index_title = _("Traidoo")
admin.site.site_header = _("Traidoo Administration")
admin.site.site_title = _("Traidoo Administration")

urlpatterns = [
    path("", include("carts.urls")),
    url(
        r"^orders/cron/find-unsold-items/(?P<seller_id>.+)",
        FindUnsoldItemsView.as_view(),
    ),
    url(r"^orders/cron/find-unsold-items", FindUnsoldItemsView.as_view()),
    url(r"^items/stats", ItemsStatsView.as_view()),
    url(r"^carts/cron/delete-inactive-carts", DeleteInactiveCartsView.as_view()),
    url(r"^users/(?P<user_id>.+)/mangopay/create", CreateMangopayAccountView.as_view()),
    url(r"^", include(router.urls)),
    url(r"^", include(product_items_router.urls)),
    url(r"^api-auth/", include("rest_framework.urls")),
    path(r"documents/", include("documents.urls")),
    url(r"^mangopay/", include("payments.urls")),
    url(r"^users/cron/delete-not-verified-users", DeleteNotVerifiedUsersView.as_view()),
    url(r"^registration", RegistrationViewSet.as_view(), name="registration"),
    url(
        r"^users/profile/personal",
        UserPersonalProfileViewSet.as_view(),
        name="user-personal-profile",
    ),
    url(
        r"^users/profile/documents/mangopay",
        MangopayDocumentsView.as_view(),
        name="user-company-documents-mangopay",
    ),
    url(
        r"^users/profile/documents",
        UserDocumentsProfileViewSet.as_view(),
        name="user-company-documents",
    ),
    url(
        r"^users/profile/company",
        UserCompanyProfileViewSet.as_view(),
        name="user-company-profile",
    ),
    url(
        r"^users/profile",
        UserProfileViewSet.as_view(),
        kwargs={"pk": "me"},
        name="user-profile",
    ),
    url(
        r"^users/mangopay/documents/(?P<document_id>.+)",
        UploadUserMangopayKycDocumentView.as_view(),
        name="user-mangopay-documents",
    ),
    path(
        r"routes/<int:route_id>/calculate_route_length",
        CalculateRouteLengthView.as_view(),
    ),
    path(r"", include("checkout.urls")),
    path(r"", include("settings.urls")),
    path(r"", include("jobs.urls")),
    path(r"", include("features.urls")),
    path(r"", include("orders.urls")),
    path(r"sellers/", include("sellers.urls")),
    path(r"", include("overlays.urls")),
    path(r"auth/", include("users.urls")),
    url(r"^docs/", include_docs_urls(title="Traidoo Documentation", public=False)),
    url(r"^_ah/warmup", warmup),
    url(r"^tinymce/", include("tinymce.urls")),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="common/robots.txt", content_type="text/plain"
        ),
    ),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    url(r"^admin_tools/", include("admin_tools.urls")),
    path(
        "admin/documents/<int:document_id>/downlolad",
        DownloadDocumentAdminView.as_view(),
        name="admin-document-download",
    ),
)
