from django.db.models import (
    Q,
    Min,
    Prefetch,
)

from catalog.models import (
    Product,
    ProductVariant,
)
from catalog.models import Category
from catalog.selectors.category_selectors import (
    get_all_child_categories
)

def get_user_filtered_products(params):

    search = params.get("search", "")

    category = params.get("category")

    min_price = params.get("min_price")

    max_price = params.get("max_price")

    color = params.get("color")

    room_type = params.get("room_type")

    sort = params.get("sort")

    products = Product.objects.select_related(
    "category"
).prefetch_related(
    "room_types",

    Prefetch(
        "variants",
        queryset=ProductVariant.objects.filter(
            is_active=True
        ).prefetch_related(
            "images"
        )
    )

).filter(
    is_active=True,
    category__is_active=True,
    variants__is_active=True,
).annotate(
    min_price=Min("variants__price")
)

    featured_raw = (params.get("featured") or "").strip().lower()

    if featured_raw in (
        "1",
        "true",
        "yes",
    ):

        products = products.filter(
            is_featured=True,
        )

    

    if search:

        products = products.filter(

            Q(name__icontains=search)

            |

            Q(brand__icontains=search)

            |

            Q(category__name__icontains=search)
        )

    

    if category:

        try:

            selected_category = Category.objects.get(
                slug=category,
                is_active=True
            )

            category_list = get_all_child_categories(
                selected_category
            )

            products = products.filter(
                category__in=category_list
            )

        except Category.DoesNotExist:

            products = products.none()



    # =========================
    # ROOM TYPE FILTER
    # =========================

    if room_type:

        products = products.filter(
            room_types__slug=room_type,
            room_types__is_active=True
        )

    

    brand_param = (params.get("brand") or "").strip()

    if brand_param:

        products = products.filter(
            brand__icontains=brand_param,
            variants__is_active=True,
        )

    

    if color:

        products = products.filter(
            variants__color__iexact=color,
            variants__is_active=True
        )

    

    if min_price:

        products = products.filter(
            variants__price__gte=min_price,
            variants__is_active=True
        )


    if max_price:

        products = products.filter(
            variants__price__lte=max_price,
            variants__is_active=True
        )

    products = products.distinct()


    if sort == "price_low":

        products = products.order_by(
    "min_price"
)

    elif sort == "price_high":

        products = products.order_by(
    "-min_price"
)

    elif sort == "a_z":

        products = products.order_by(
            "name"
        )

    elif sort == "z_a":

        products = products.order_by(
            "-name"
        )

    elif sort == "oldest":

        products = products.order_by(
            "created_at"
        )

    else:

        products = products.order_by(
            "-created_at"
        )

    return products


def get_admin_filtered_products(params):

    search = params.get("search", "")

    category = params.get("category")

    room_type = params.get("room_type")

    sort = params.get("sort")
    is_active = params.get("is_active")

    products = Product.objects.select_related(
        "category"
    ).prefetch_related(
        "room_types",

        Prefetch(
            "variants",
            queryset=ProductVariant.objects.prefetch_related(
                "images"
            )
        )

    ).annotate(
        min_price=Min("variants__price")
    )

    

    if search:

        products = products.filter(

            Q(name__icontains=search)

            |

            Q(brand__icontains=search)

            |

            Q(category__name__icontains=search)
        )

   

    if is_active == "true":

        products = products.filter(
            is_active=True
        )

    elif is_active == "false":

        products = products.filter(
            is_active=False
        )
        
    
    

    if category:

        try:

            selected_category = Category.objects.get(
                slug=category
            )

            category_list = get_all_child_categories(
                selected_category
            )

            products = products.filter(
                category__in=category_list
            )

        except Category.DoesNotExist:

            products = products.none()


    

    if room_type:

        products = products.filter(
            room_types__slug=room_type
            
        )

    products = products.distinct()
 

    if sort == "price_low":

        products = products.order_by(
            "min_price"
        )

    elif sort == "price_high":

        products = products.order_by(
            "-min_price"
        )

    elif sort == "a_z":

        products = products.order_by(
            "name"
        )

    elif sort == "z_a":

        products = products.order_by(
            "-name"
        )

    elif sort == "oldest":

        products = products.order_by(
            "created_at"
        )

    else:

        products = products.order_by(
            "-created_at"
        )

    return products