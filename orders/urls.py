from django.urls import path

from orders.views import (
    OrderCancelView,
    OrderCreateView,
    OrderDetailView,
    OrderInvoicePdfView,
    OrderLineCancelView,
    OrderLineReturnCreateView,
    RazorpayInitiateView,
    RazorpayVerifyView,
    RazorpayWebhookView,
    UserPurchasesListView,
)

urlpatterns = [
    path(
        "razorpay/initiate/",
        RazorpayInitiateView.as_view(),
    ),
    path(
        "razorpay/verify/",
        RazorpayVerifyView.as_view(),
    ),
    path(
        "razorpay/webhook/",
        RazorpayWebhookView.as_view(),
    ),
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
