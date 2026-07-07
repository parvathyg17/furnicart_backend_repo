from django.urls import path
from accounts.views.contact_views import AdminContactMessageListView, AdminContactMessageDetailView

urlpatterns = [
    path("", AdminContactMessageListView.as_view(), name="admin-contact-messages"),
    path("<int:pk>/", AdminContactMessageDetailView.as_view(), name="admin-contact-messages-detail"),
]
