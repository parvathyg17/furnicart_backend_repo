from django.urls import path
from catalog.views.user.room_type_views import (
    UserRoomTypeListView
)

from catalog.views.user.product_views import (
    UserProductListView,
    UserProductDetailView,
)

from catalog.views.user.category_views import (
    UserCategoryListView
)

urlpatterns = [

    path(
        "products/",
        UserProductListView.as_view()
    ),

    path(
        "products/<int:product_id>/",
        UserProductDetailView.as_view()
    ),

    path(
        "categories/",
        UserCategoryListView.as_view()
    ),

    path(
    "room-types/",
    UserRoomTypeListView.as_view()
),
]