from django.urls import path

from .views import (
    AddressView,
    AddressDetailView,
    SetDefaultAddressView
)

urlpatterns = [

    path(
        '',
        AddressView.as_view()
    ),

    path(
        '<int:pk>/',
        AddressDetailView.as_view()
    ),

    path(
        '<int:pk>/set-default/',
        SetDefaultAddressView.as_view()
    ),
]