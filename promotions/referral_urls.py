from django.urls import path

from promotions.views.referral_views import ReferralMeView

urlpatterns = [

    path(
        "referral/me/",
        ReferralMeView.as_view(),
    ),

]
