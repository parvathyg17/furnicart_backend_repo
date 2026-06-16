from rest_framework.routers import SimpleRouter

from catalog.views.admin.room_type_views import AdminRoomTypeViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", AdminRoomTypeViewSet, basename="admin-room-type")

urlpatterns = router.urls
