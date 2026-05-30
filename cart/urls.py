from django.urls import path

from cart.views import (
    CartView,
    CartItemDetailView,
    CartCheckoutValidateView,
)

urlpatterns = [

    path(
        "",
        CartView.as_view(),
    ),

    path(
        "validate-checkout/",
        CartCheckoutValidateView.as_view(),
    ),

    path(
        "items/<int:item_id>/",
        CartItemDetailView.as_view(),
    ),
]
