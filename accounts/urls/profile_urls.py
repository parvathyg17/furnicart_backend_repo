from django.urls import path

from accounts.views.profile_views import (
    EmailChangeRequestView,
    EmailChangeVerifyView,
    UserProfileView,
)
from accounts.views.wallet_views import (
    WalletTransactionListView,
    WalletView,
)

urlpatterns = [
    path('', UserProfileView.as_view()),
    path('email-change/request/', EmailChangeRequestView.as_view()),
    path('email-change/verify/', EmailChangeVerifyView.as_view()),
    path('wallet/', WalletView.as_view()),
    path('wallet/transactions/', WalletTransactionListView.as_view()),
]