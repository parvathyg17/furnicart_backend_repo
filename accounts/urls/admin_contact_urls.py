from django.urls import path

from accounts.views.contact_views import (AdminContactMessageDetailView,
                                          AdminContactMessageListView)

urlpatterns = [
    path("", AdminContactMessageListView.as_view(), name="admin-contact-messages"),
    path(
        "<int:pk>/",
        AdminContactMessageDetailView.as_view(),
        name="admin-contact-messages-detail",
    ),
]
