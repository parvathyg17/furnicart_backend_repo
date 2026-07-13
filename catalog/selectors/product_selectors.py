from django.db.models import Count, Max, Min, Prefetch, Q, F, Case, When, Value, DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce, Least
from django.utils import timezone
from promotions.models import Offer

from catalog.models import Category, Product, ProductVariant
from catalog.selectors.category_selectors import get_all_child_categories
from catalog.selectors.review_selectors import annotate_product_ratings

LISTABLE_VARIANT_FILTER = Q(
    variants__is_active=True,
    variants__stock__gt=0,
)


def annotate_catalog_prices(
    queryset,
):

    in_stock_min = Subquery(
        ProductVariant.objects.filter(
            product=OuterRef("id"),
            is_active=True,
            stock__gt=0,
        ).order_by("price").values("price")[:1]
    )

    in_stock_max = Subquery(
        ProductVariant.objects.filter(
            product=OuterRef("id"),
            is_active=True,
            stock__gt=0,
        ).order_by("-price").values("price")[:1]
    )

    active_min = Subquery(
        ProductVariant.objects.filter(
            product=OuterRef("id"),
            is_active=True,
        ).order_by("price").values("price")[:1]
    )

    active_max = Subquery(
        ProductVariant.objects.filter(
            product=OuterRef("id"),
            is_active=True,
        ).order_by("-price").values("price")[:1]
    )

    return queryset.annotate(
        catalog_min_price=Coalesce(
            in_stock_min,
            active_min,
        ),
        catalog_max_price=Coalesce(
            in_stock_max,
            active_max,
        ),
    )


def annotate_effective_prices(queryset):
    now = timezone.now()

    applicable_offers = Offer.objects.filter(
        is_active=True,
    ).filter(
        Q(valid_from__lte=now) | Q(valid_from__isnull=True)
    ).filter(
        Q(valid_until__gte=now) | Q(valid_until__isnull=True)
    ).filter(
        Q(offer_type=Offer.OfferType.PRODUCT, product_id=OuterRef("id")) |
        Q(offer_type=Offer.OfferType.CATEGORY, category_id=OuterRef("category_id"))
    )

    discount_amount = Case(
        When(
            discount_type=Offer.DiscountType.PERCENT,
            then=Least(
                (OuterRef("catalog_min_price") * F("discount_value")) / Value(100.0, output_field=DecimalField()),
                Coalesce(F("max_discount_amount"), OuterRef("catalog_min_price"))
            )
        ),
        When(
            discount_type=Offer.DiscountType.FIXED,
            then=Least(F("discount_value"), OuterRef("catalog_min_price"))
        ),
        output_field=DecimalField()
    )

    best_discount_subquery = applicable_offers.annotate(
        calculated_discount=discount_amount
    ).order_by("-calculated_discount").values("calculated_discount")[:1]

    discount_amount_max = Case(
        When(
            discount_type=Offer.DiscountType.PERCENT,
            then=Least(
                (OuterRef("catalog_max_price") * F("discount_value")) / Value(100.0, output_field=DecimalField()),
                Coalesce(F("max_discount_amount"), OuterRef("catalog_max_price"))
            )
        ),
        When(
            discount_type=Offer.DiscountType.FIXED,
            then=Least(F("discount_value"), OuterRef("catalog_max_price"))
        ),
        output_field=DecimalField()
    )

    best_discount_max_subquery = applicable_offers.annotate(
        calculated_discount=discount_amount_max
    ).order_by("-calculated_discount").values("calculated_discount")[:1]

    return queryset.annotate(
        best_discount=Coalesce(Subquery(best_discount_subquery), Value(0, output_field=DecimalField())),
        best_discount_max=Coalesce(Subquery(best_discount_max_subquery), Value(0, output_field=DecimalField()))
    ).annotate(
        effective_price=F("catalog_min_price") - F("best_discount"),
        effective_max_price=F("catalog_max_price") - F("best_discount_max")
    )


def get_user_filtered_products(params):

    search = params.get("search", "")

    category = params.get("category")

    min_price = params.get("min_price")

    max_price = params.get("max_price")

    color = params.get("color")

    room_type = params.get("room_type")

    sort = params.get("sort")

    products = (
        Product.objects.select_related("category")
        .prefetch_related(
            "room_types",
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True).prefetch_related(
                    "images"
                ),
            ),
        )
        .filter(
            is_active=True,
            category__is_active=True,
            variants__is_active=True,
        )
    )
   

    products = annotate_catalog_prices(
        products,
    )

    products = annotate_effective_prices(
        products,
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
            | Q(brand__icontains=search)
            | Q(category__name__icontains=search)
        )

    if category:

        try:

            selected_category = Category.objects.get(slug=category, is_active=True)

            category_list = get_all_child_categories(selected_category)

            products = products.filter(category__in=category_list)

        except Category.DoesNotExist:

            products = products.none()

    if room_type:

        products = products.filter(
            room_types__slug=room_type, room_types__is_active=True
        )

    brand_param = (params.get("brand") or "").strip()

    if brand_param:

        products = products.filter(
            brand__icontains=brand_param,
            variants__is_active=True,
        )

    if color:

        products = products.filter(
            LISTABLE_VARIANT_FILTER,
            variants__color__iexact=color,
        )

    if min_price:

        products = products.filter(
            effective_max_price__gte=min_price,
        )

    if max_price:

        products = products.filter(
            effective_price__lte=max_price,
        )

    products = products.distinct()

    if sort == "price_low":

        products = products.order_by(
            "effective_price",
        )

    elif sort == "price_high":

        products = products.order_by(
            "-effective_max_price",
        )

    elif sort == "a_z":

        products = products.order_by("name")

    elif sort == "z_a":

        products = products.order_by("-name")

    elif sort == "oldest":

        products = products.order_by("created_at")

    else:

        products = products.order_by("-created_at")

    return annotate_product_ratings(
        products,
    )


def get_admin_filtered_products(params):

    search = params.get("search", "")

    category = params.get("category")

    room_type = params.get("room_type")

    sort = params.get("sort")
    is_active = params.get("is_active")

    products = Product.objects.select_related("category").prefetch_related(
        "room_types",
        Prefetch(
            "variants", queryset=ProductVariant.objects.prefetch_related("images")
        ),
    )

    products = annotate_catalog_prices(
        products,
    )

    if search:

        products = products.filter(
            Q(name__icontains=search)
            | Q(brand__icontains=search)
            | Q(category__name__icontains=search)
        )

    if is_active == "true":

        products = products.filter(is_active=True)

    elif is_active == "false":

        products = products.filter(is_active=False)

    if category:

        try:

            selected_category = Category.objects.get(slug=category)

            category_list = get_all_child_categories(selected_category)

            products = products.filter(category__in=category_list)

        except Category.DoesNotExist:

            products = products.none()

    if room_type:

        products = products.filter(room_types__slug=room_type)

    products = products.distinct()

    if sort == "price_low":

        products = products.order_by(
            "catalog_min_price",
        )

    elif sort == "price_high":

        products = products.order_by(
            "-catalog_max_price",
        )

    elif sort == "a_z":

        products = products.order_by("name")

    elif sort == "z_a":

        products = products.order_by("-name")

    elif sort == "oldest":

        products = products.order_by("created_at")

    else:

        products = products.order_by("-created_at")

    return products
