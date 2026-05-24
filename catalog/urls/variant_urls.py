from django.urls import path

from catalog.views.admin.variant_views import (
    ProductVariantCreateView,
    ProductVariantDetailView,
    VariantImageDeleteView,
    ProductVariantToggleStatusView,
)

urlpatterns = [

    # CREATE VARIANT

    path(
        "<int:product_id>/variants/",
        ProductVariantCreateView.as_view()
    ),

    # UPDATE VARIANT

    path(
        "variants/<int:variant_id>/",
        ProductVariantDetailView.as_view()
    ),

    # TOGGLE STATUS

    path(
        "variants/<int:variant_id>/toggle-status/",
        ProductVariantToggleStatusView.as_view()
    ),

    # DELETE IMAGE

    path(
        "variant-images/<int:image_id>/",
        VariantImageDeleteView.as_view()
    ),
]