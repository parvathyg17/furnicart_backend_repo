from django.urls import path

from catalog.views.admin.room_type_views import (
    RoomTypeListCreateView,
    RoomTypeDetailView,
    RoomTypeSoftDeleteView,
)

urlpatterns = [

    path(
        "",
        RoomTypeListCreateView.as_view()
    ),

    path(
        "<int:room_type_id>/",
        RoomTypeDetailView.as_view()
    ),

    path(
        "<int:room_type_id>/delete/",
        RoomTypeSoftDeleteView.as_view()
    ),
]