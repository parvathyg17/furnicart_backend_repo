from django.urls import path

from orders.views import OrderCreateView, OrderDetailView

urlpatterns = [
    path(
        "",
        OrderCreateView.as_view(),
    ),
    path(
        "<str:order_number>/",
        OrderDetailView.as_view(),
    ),
]
