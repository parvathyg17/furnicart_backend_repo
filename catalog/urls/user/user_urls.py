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

from catalog.views.user.review_views import (
    EligibleReviewProductsView,
    ProductReviewEligibilityView,
    ProductReviewListCreateView,
    UserReviewDetailView,
    UserReviewListView,
)

urlpatterns = [

    path(
        "products/",
        UserProductListView.as_view()
    ),

    path(
        "products/<str:product_ref>/",
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

    path(
        "products/<str:product_ref>/reviews/",
        ProductReviewListCreateView.as_view(),
    ),

    path(
        "products/<str:product_ref>/review-eligibility/",
        ProductReviewEligibilityView.as_view(),
    ),

    path(
        "reviews/mine/",
        UserReviewListView.as_view(),
    ),

    path(
        "reviews/eligible/",
        EligibleReviewProductsView.as_view(),
    ),

    path(
        "reviews/<int:review_id>/",
        UserReviewDetailView.as_view(),
    ),
]