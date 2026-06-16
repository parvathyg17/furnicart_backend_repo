from django.urls import path

from catalog.views.admin.review_views import (
    AdminReviewDetailView,
    AdminReviewListView,
)

urlpatterns = [

    path(
        "",
        AdminReviewListView.as_view(),
    ),

    path(
        "<int:review_id>/",
        AdminReviewDetailView.as_view(),
    ),
]
