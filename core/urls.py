"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/admin/orders/",
        include(
            "orders.admin_urls",
        ),
    ),
    path('api/admin/', include('adminpanel.urls')),
    path('api/users/', include('accounts.urls.auth_urls')),
    path('api/profile/', include('accounts.urls.profile_urls')),
    path('api/address/', include('accounts.urls.address_urls')),
    path(
        "api/admin/categories/",
        include(
            "catalog.urls.category_urls"
        )
    ),

    

    path(
        "api/admin/products/",
        include(
            "catalog.urls.product_urls"
        )
    ),

    path(
        "api/",
        include(
            "catalog.urls.user.user_urls"
        )
    ),

    path(
        "api/admin/product-images/",
        include(
            "catalog.urls.image_urls"
        )
    ),
    path(
        "api/admin/products/",
        include(
            "catalog.urls.variant_urls"
        )
    ),

    path(
        "api/admin/room-types/",
        include(
            "catalog.urls.room_type_urls"
        )
    ),

    path(
        "api/admin/inventory/",
        include(
            "catalog.urls.inventory_urls",
        ),
    ),

    path(
        "api/cart/",
        include(
            "cart.urls"
        )
    ),

    path(
        "api/wishlist/",
        include(
            "wishlist.urls"
        )
    ),

    path(
        "api/orders/",
        include(
            "orders.urls"
        )
    ),
  
    

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)