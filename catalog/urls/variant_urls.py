from django.urls import path

from catalog.views.admin.variant_views import (
    ProductVariantCreateView,
    ProductVariantDetailView,
    VariantImageDeleteView,
    ProductVariantToggleStatusView,
)

urlpatterns = [

    

    path(
        "<int:product_id>/variants/",
        ProductVariantCreateView.as_view()
    ),

    

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