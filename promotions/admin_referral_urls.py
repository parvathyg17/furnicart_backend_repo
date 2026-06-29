from django.urls import path

from promotions.views.admin_referral_views import (
    AdminReferralProgramView,
)

urlpatterns = [

    path(
        "referral-program/",
        AdminReferralProgramView.as_view(),
    ),

]
