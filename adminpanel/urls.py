from django.urls import path

from .views import AdminLoginView, AdminLogoutView, AdminMeView, BlockUserView, UserListView

urlpatterns = [
    path('login/', AdminLoginView.as_view()),
    path('users/', UserListView.as_view()),
    path('users/<int:user_id>/block/', BlockUserView.as_view()),
    path('logout/', AdminLogoutView.as_view()),
    path("me/", AdminMeView.as_view()),
]

