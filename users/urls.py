from django.urls import path
from .views import ForgotPasswordView, ResendOTPView, ResetPasswordView, SignupView, LoginView, VerifyOTPView

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('login/', LoginView.as_view()),
    path('verify-otp/', VerifyOTPView.as_view()),
    path('resend-otp/', ResendOTPView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    
]