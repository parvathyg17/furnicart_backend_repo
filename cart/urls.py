from django.urls import path

from cart.views import (
    CartView,
    CartItemDetailView,
    CartCheckoutValidateView,
    CartCheckoutPreviewView,
    CartCouponView,
    CartAvailableCouponsView,
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
        "checkout-preview/",
        CartCheckoutPreviewView.as_view(),
    ),

    path(
        "coupon/",
        CartCouponView.as_view(),
    ),

    path(
        "available-coupons/",
        CartAvailableCouponsView.as_view(),
    ),

    path(
        "items/<int:item_id>/",
        CartItemDetailView.as_view(),
    ),
]
