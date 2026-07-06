from django.urls import path
from accounts.views.contact_views import PublicContactMessageView

urlpatterns = [
    path("", PublicContactMessageView.as_view(), name="public-contact-messages"),
]
