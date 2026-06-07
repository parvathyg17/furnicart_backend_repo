from django.urls import path

from catalog.views.admin.inventory_views import AdminVariantStockListView

urlpatterns = [
    path(
        "",
        AdminVariantStockListView.as_view(),
    ),
]
