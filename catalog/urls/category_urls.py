from rest_framework.routers import SimpleRouter

from catalog.views.admin.category_views import AdminCategoryViewSet

router = SimpleRouter(trailing_slash=True)
router.register("", AdminCategoryViewSet, basename="admin-category")

urlpatterns = router.urls
