from django.db import transaction

from rest_framework import serializers


from catalog.models import (
    Product,
    ProductVariant,
    VariantImage,
    RoomType,
)
from catalog.serializers.room_type_serializers import (
    RoomTypeSerializer
)

from catalog.selectors.recommendation_selectors import (
        get_related_products
    )

from catalog.services.product_services import (
    validate_product_can_activate,
    validate_variant_fields_and_images,
)

# =====================================================
# VARIANT IMAGE SERIALIZER
# =====================================================

class VariantImageSerializer(
    serializers.ModelSerializer
):

    image_url = serializers.SerializerMethodField()

    class Meta:

        model = VariantImage

        fields = [
            "id",
            "image",
            "image_url",
            "is_primary",
            "display_order",
        ]

    def get_image_url(self, obj):

        request = self.context.get("request")

        if obj.image and request:

            return request.build_absolute_uri(
                obj.image.url
            )

        return None
    
    


# =====================================================
# PRODUCT VARIANT SERIALIZER
# =====================================================

class ProductVariantSerializer(
    serializers.ModelSerializer
):

    images = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()

    class Meta:

        model = ProductVariant

        fields = [
        "id",
        "variant_name",
        "color",
        "size",
        "material",
        "price",
        "stock",
        "sku",
        "is_active",
        "images",
        "image_count",
]

    def get_images(self, obj):

        request = self.context.get("request")

        serializer = VariantImageSerializer(
           obj.images.order_by(
               "display_order",
               "-created_at"
               ),
            many=True,
            context={
                "request": request
            }
        )

        return serializer.data
    def get_image_count(self, obj):

        return obj.images.count()

    def validate_price(self, value):

        if value <= 0:

            raise serializers.ValidationError(
                "Price must be greater than 0"
            )

        return value

    def validate_stock(self, value):

        if value < 0:

            raise serializers.ValidationError(
                "Stock cannot be negative"
            )

        return value
    
    def validate_sku(self, value):

        cleaned = (value or "").strip()

        if not cleaned:

            raise serializers.ValidationError(
                "SKU is required."
            )

        queryset = ProductVariant.objects.filter(
            sku=cleaned
        )

        # EXCLUDE CURRENT VARIANT DURING UPDATE

        if self.instance:

            queryset = queryset.exclude(
                id=self.instance.id
            )

        if queryset.exists():

            raise serializers.ValidationError(
                "SKU already exists"
            )

        return cleaned

    def _strip_required(
        self,
        value,
        label,
    ):

        if value is None:

            raise serializers.ValidationError(
                f"{label} is required."
            )

        cleaned = str(value).strip()

        if not cleaned:

            raise serializers.ValidationError(
                f"{label} is required."
            )

        return cleaned

    def validate_variant_name(
        self,
        value,
    ):

        return self._strip_required(
            value,
            "Variant name",
        )

    def _strip_optional_text(
        self,
        value,
    ):

        """
        Allow blank / null on write; completeness for active
        variants is enforced in validate() and on activation.
        """

        if value is None:

            return None

        cleaned = str(value).strip()

        if not cleaned:

            return None

        return cleaned

    def validate_color(
        self,
        value,
    ):

        return self._strip_optional_text(
            value,
        )

    def validate_material(
        self,
        value,
    ):

        return self._strip_optional_text(
            value,
        )

    def validate_size(
        self,
        value,
    ):

        return self._strip_optional_text(
            value,
        )

    def validate(self, attrs):

        instance = self.instance

        if instance is None:

            create_active = attrs.get(
                "is_active",
                False,
            )

            attrs["is_active"] = create_active

            if create_active:

                for field, label in (

                    (
                        "color",
                        "Color / finish",
                    ),

                    (
                        "material",
                        "Material",
                    ),

                    (
                        "size",
                        "Size / dimensions",
                    ),
                ):

                    raw = attrs.get(
                        field,
                    )

                    if (
                        raw is None
                        or not str(raw).strip()
                    ):

                        raise serializers.ValidationError(
                            {
                                field: (
                                    f"{label} is required "
                                    "when the variant is active."
                                ),
                            }
                        )

            return attrs

        will_active = attrs.get(
            "is_active",
            instance.is_active,
        )

        if not will_active:

            return attrs

        old_values = {}

        try:

            allowed_keys = {

                "variant_name",

                "sku",

                "price",

                "stock",

                "color",

                "material",

                "size",

                "is_active",
            }

            for key, val in attrs.items():

                if key not in allowed_keys:

                    continue

                old_values[key] = getattr(
                    instance,
                    key,
                )

                setattr(
                    instance,
                    key,
                    val,
                )

            ok, err = validate_variant_fields_and_images(
                instance,
            )

            if not ok:

                raise serializers.ValidationError(
                    {
                        "is_active": err,
                    }
                )

        finally:

            for key, val in old_values.items():

                setattr(
                    instance,
                    key,
                    val,
                )

        return attrs

class ProductSerializer(
    serializers.ModelSerializer
):

    variants = ProductVariantSerializer(
        many=True,
        required=False
    )

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    room_types = RoomTypeSerializer(
        many=True,
        read_only=True
    )

    room_type_ids = serializers.PrimaryKeyRelatedField(
        queryset=RoomType.objects.filter(
            is_active=True
        ),
        many=True,
        write_only=True,
        required=False
    )

    thumbnail = serializers.SerializerMethodField()

    related_products = serializers.SerializerMethodField(
    read_only=True)

    breadcrumbs = serializers.SerializerMethodField()

    stock_status = serializers.SerializerMethodField()

    class Meta:

        model = Product

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "brand",
            "category",
            "category_name",
            "room_types",
            "room_type_ids",
            "breadcrumbs",
            "thumbnail",
            "stock_status",
            "related_products",
            "is_active",
            "is_featured",
            "variants",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.context.get("exclude_related"):

            self.fields.pop(
                "related_products",
                None
            )

    def get_thumbnail(self, obj):

        request = self.context.get("request")

        primary_image = None

        # =========================
        # USE PREFETCHED DATA
        # =========================

        for variant in obj.variants.all():

            if not variant.is_active:
                continue

            images = sorted(
                variant.images.all(),
                key=lambda img: (
                    img.display_order,
                    -img.created_at.timestamp()
                )
            )

            # FIND PRIMARY IMAGE

            for image in images:

                if image.is_primary:

                    primary_image = image
                    break

            # FALLBACK FIRST IMAGE

            if not primary_image and images:

                primary_image = images[0]

            if primary_image:
                break

        if not primary_image:

            return None

        if request:

            return request.build_absolute_uri(
                primary_image.image.url
            )

        return primary_image.image.url

    def validate_name(self, value):

        cleaned = (value or "").strip()

        if not cleaned:

            raise serializers.ValidationError(
                "Product name is required."
            )

        queryset = Product.objects.filter(
            name__iexact=cleaned
        )

        if self.instance:

            queryset = queryset.exclude(
                id=self.instance.id
            )

        if queryset.exists():

            raise serializers.ValidationError(
                "Product name already exists."
            )

        return cleaned

    def validate_category(self, value):

        if not value.is_active:

            raise serializers.ValidationError(
                "Cannot add product to inactive category"
            )

        return value

    def validate(self, attrs):

        variants = attrs.get(
            "variants",
            [],
        )

        sku_list = []

        for variant in variants:

            sku = variant.get("sku")

            if sku in sku_list:

                raise serializers.ValidationError(
                    {
                        "sku":
                            f"Duplicate SKU found: {sku}"
                    }
                )

            sku_list.append(sku)

            if self.instance is None:

                if ProductVariant.objects.filter(
                    sku=sku
                ).exists():

                    raise serializers.ValidationError(
                        {
                            "sku":
                                f"SKU already exists: {sku}"
                        }
                    )

        if self.instance is None:

            if not (attrs.get("name") or "").strip():

                raise serializers.ValidationError(
                    {
                        "name":
                            "Product name is required.",
                    }
                )

            if not (attrs.get("description") or "").strip():

                raise serializers.ValidationError(
                    {
                        "description":
                            "Description is required.",
                    }
                )

            room_types = attrs.get(
                "room_type_ids",
            )

            if (
                not room_types
                or len(room_types) < 1
            ):

                raise serializers.ValidationError(
                    {
                        "room_type_ids":
                            "Select at least one room type.",
                    }
                )

        else:

            merged_active = attrs.get(
                "is_active",
                self.instance.is_active,
            )

            if not merged_active:

                return attrs

            merged_desc = attrs.get(
                "description",
                self.instance.description,
            )

            rooms_arg = (

                attrs["room_type_ids"]

                if "room_type_ids" in attrs

                else None
            )

            if not self.instance.is_active:

                ok, err = validate_product_can_activate(
                    self.instance,
                    description=merged_desc,
                    room_type_ids=rooms_arg,
                )

                if not ok:

                    raise serializers.ValidationError(
                        {
                            "is_active": err,
                        }
                    )

            else:

                if not (merged_desc or "").strip():

                    raise serializers.ValidationError(
                        {
                            "description":
                                "Description is required.",
                        }
                    )

                if (
                    rooms_arg is not None
                    and len(rooms_arg) < 1
                ):

                    raise serializers.ValidationError(
                        {
                            "room_type_ids":
                                "Select at least one room type.",
                        }
                    )

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        validated_data["is_active"] = False

        variants_data = validated_data.pop(
            "variants",
            []
        )

        room_types = validated_data.pop(
        "room_type_ids",
        []
        )

        product = Product.objects.create(
            **validated_data
        )

        product.room_types.set(
            room_types
        )

        for variant_data in variants_data:

            ProductVariant.objects.create(
                product=product,
                **variant_data
            )

        return product
    
    @transaction.atomic
    def update(
        self,
        instance,
        validated_data
    ):

        validated_data.pop(
            "variants",
            None
        )

        room_types = validated_data.pop(
            "room_type_ids",
            None
        )


        for attr, value in validated_data.items():

            setattr(instance, attr, value)

        instance.save()

        if room_types is not None:

            instance.room_types.set(
                room_types
            )

        

        return instance

    def get_related_products(self, obj):

   
        request = self.context.get("request")

        related_products = get_related_products(obj)

        serializer = ProductSerializer(
            related_products,
            many=True,
            context={
                "request": request,
                "exclude_related": True
            }
        )

        return serializer.data
    
    
    
    # def to_representation(self, instance):

    #     representation = super().to_representation(
    #         instance
    #     )

    #     if self.context.get("exclude_related"):

    #         representation.pop(
    #             "related_products",
    #             None
    #         )

    #     return representation
    
    def get_breadcrumbs(self, obj):

        breadcrumbs = []

        category = obj.category

        while category:

            breadcrumbs.insert(0, {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
            })

            category = category.parent

        return breadcrumbs
    

    def get_stock_status(self, obj):

        total_stock = sum(

            variant.stock

            for variant in obj.variants.all()

            if variant.is_active
        )

        if total_stock <= 0:

            return "out_of_stock"

        if total_stock <= 5:

            return "low_stock"

        return "in_stock"