from django.urls import path

from catalog.views.admin.variant_views import (
    ProductVariantDetailView,
    VariantImageDeleteView,
    ProductVariantToggleStatusView,
)

urlpatterns = [

    path(
        "variants/<int:variant_id>/",
        ProductVariantDetailView.as_view()
    ),

    path(
        "variants/<int:variant_id>/toggle-status/",
        ProductVariantToggleStatusView.as_view()
    ),

    path(
        "variant-images/<int:image_id>/",
        VariantImageDeleteView.as_view()
    ),
]