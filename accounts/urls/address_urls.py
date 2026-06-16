from rest_framework.routers import SimpleRouter

from accounts.views.address_views import AddressViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", AddressViewSet, basename="address")

urlpatterns = router.urls
