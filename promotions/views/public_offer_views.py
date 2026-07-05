from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from promotions.models import Offer
from promotions.serializers import PublicOfferSerializer


class PublicOfferListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicOfferSerializer

    def get_queryset(self):
        return Offer.objects.filter(is_active=True).exclude(image__isnull=True).exclude(image='')