from django.urls import path

from promotions.views.public_offer_views import PublicOfferListView

urlpatterns = [
    path("banners/", PublicOfferListView.as_view(), name="public-offers"),
]
