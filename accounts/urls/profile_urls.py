from django.urls import path
from accounts.views.profile_views import EmailChangeRequestView, EmailChangeVerifyView, UserProfileView

urlpatterns = [
    path('', UserProfileView.as_view()),
    path('email-change/request/', EmailChangeRequestView.as_view()),
    path('email-change/verify/', EmailChangeVerifyView.as_view()),
    
]