from django.urls import path

from catalog.views.admin.product_views import (
    ProductListCreateView,
    ProductDetailView,
    ProductSoftDeleteView,
    ProductToggleStatusView,
)

urlpatterns = [

    path(
        "",
        ProductListCreateView.as_view()
    ),

    path(
        "<int:product_id>/",
        ProductDetailView.as_view()
    ),

    path(
        "<int:product_id>/delete/",
        ProductSoftDeleteView.as_view()
    ),

    path(
        "<int:product_id>/toggle-status/",
        ProductToggleStatusView.as_view()
    ),
]