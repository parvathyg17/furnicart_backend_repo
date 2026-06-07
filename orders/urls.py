from django.urls import path

from orders.views import (
    OrderCancelView,
    OrderCreateView,
    OrderDetailView,
    OrderInvoicePdfView,
    OrderLineCancelView,
    OrderLineReturnCreateView,
    UserPurchasesListView,
)

urlpatterns = [
    path(
        "purchases/",
        UserPurchasesListView.as_view(),
    ),
    path(
        "",
        OrderCreateView.as_view(),
    ),
    path(
        "<str:order_number>/lines/<int:line_id>/return/",
        OrderLineReturnCreateView.as_view(),
    ),
    path(
        "<str:order_number>/lines/<int:line_id>/cancel/",
        OrderLineCancelView.as_view(),
    ),
    path(
        "<str:order_number>/cancel/",
        OrderCancelView.as_view(),
    ),
    path(
        "<str:order_number>/invoice/",
        OrderInvoicePdfView.as_view(),
    ),
    path(
        "<str:order_number>/",
        OrderDetailView.as_view(),
    ),
]
