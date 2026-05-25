from django.urls import path

from catalog.views.admin.category_views import (
    CategoryListCreateView,
    CategoryDetailView,
    CategoryRestoreView,
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
    path(
            "<int:category_id>/restore/",
            CategoryRestoreView.as_view()
        ),
]