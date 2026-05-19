from django.urls import path

from catalog.views.admin.image_views import (
    VariantImageUploadView
)

urlpatterns = [

    path(
        "",
        VariantImageUploadView.as_view()
    ),
]