from django.urls import path

from promotions.views.admin_offer_views import (
    AdminOfferDetailView,
    AdminOfferListCreateView,
)

urlpatterns = [

    path(
        "",
        AdminOfferListCreateView.as_view(),
    ),

    path(
        "<int:offer_id>/",
        AdminOfferDetailView.as_view(),
    ),

]
