from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from core.utils.token_refresh import CookieTokenRefreshView
from .views import ChangePasswordView, ForgotPasswordView, GoogleLoginView, LogoutView, MeView, ResendOTPView, ResetPasswordView, SignupView, LoginView, VerifyOTPView

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('login/', LoginView.as_view()),
    path('verify-otp/', VerifyOTPView.as_view()),
    path('resend-otp/', ResendOTPView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('google-login/', GoogleLoginView.as_view()),
    path("me/", MeView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('logout/', LogoutView.as_view()),
    path("token/refresh/", CookieTokenRefreshView.as_view()),
]