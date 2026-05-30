from django.urls import path

from .views import (
    WishlistListView,
    WishlistToggleView,
)

urlpatterns = [

    path(
        "",
        WishlistListView.as_view(),
    ),

    path(
        "toggle/",
        WishlistToggleView.as_view(),
    ),
]
