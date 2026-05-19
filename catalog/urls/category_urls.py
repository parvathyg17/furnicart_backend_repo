from django.urls import path

from catalog.views.admin.category_views import (
    CategoryListCreateView,
    CategoryDetailView,
    CategorySoftDeleteView,
)

urlpatterns = [

    path(
        "",
        CategoryListCreateView.as_view()
    ),

    path(
        "<int:category_id>/",
        CategoryDetailView.as_view()
    ),

    path(
        "<int:category_id>/delete/",
        CategorySoftDeleteView.as_view()
    ),
]