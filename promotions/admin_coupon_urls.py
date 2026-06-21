from django.urls import path

from promotions.views.admin_coupon_views import (
    AdminCouponDetailView,
    AdminCouponListCreateView,
)

urlpatterns = [

    path(
        "",
        AdminCouponListCreateView.as_view(),
    ),

    path(
        "<int:coupon_id>/",
        AdminCouponDetailView.as_view(),
    ),

]
