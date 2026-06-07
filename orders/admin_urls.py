from django.urls import path

from orders.views.admin_order_views import (
    AdminOrderCancelView,
    AdminOrderDetailView,
    AdminOrderLineFulfillmentView,
    AdminOrderListView,
    AdminReturnDetailView,
    AdminReturnListView,
)

urlpatterns = [
    path(
        "",
        AdminOrderListView.as_view(),
    ),
    path(
        "returns/",
        AdminReturnListView.as_view(),
    ),
    path(
        "returns/<int:pk>/",
        AdminReturnDetailView.as_view(),
    ),
    path(
        "<str:order_number>/cancel/",
        AdminOrderCancelView.as_view(),
    ),
    path(
        "<str:order_number>/lines/<int:line_id>/fulfillment/",
        AdminOrderLineFulfillmentView.as_view(),
    ),
    path(
        "<str:order_number>/",
        AdminOrderDetailView.as_view(),
    ),
]
