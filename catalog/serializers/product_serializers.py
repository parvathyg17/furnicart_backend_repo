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

        queryset = ProductVariant.objects.filter(
            sku=value
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

        return value


# =====================================================
# PRODUCT SERIALIZER
# =====================================================

class ProductSerializer(
    serializers.ModelSerializer
):

    variants = ProductVariantSerializer(
        many=True
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

        primary_image = VariantImage.objects.filter(
            variant__product=obj,
            variant__is_active=True,
            is_primary=True
        ).first()

        if not primary_image:

            primary_image = VariantImage.objects.filter(
                variant__product=obj,
                variant__is_active=True
            ).order_by(
                "display_order"
            ).first()

        if not primary_image:

            return None

        if request:

            return request.build_absolute_uri(
                primary_image.image.url
            )

        return primary_image.image.url
    
    def validate_category(self, value):

        if not value.is_active:

            raise serializers.ValidationError(
                "Cannot add product to inactive category"
            )

        return value

    def validate(self, attrs):

        variants = attrs.get("variants")

        # ONLY REQUIRED DURING CREATE

        if self.instance is None and not variants:

            raise serializers.ValidationError({
                "variants":
                "At least one variant is required"
            })

        sku_list = []

        for variant in variants:

            sku = variant.get("sku")

            if sku in sku_list:

                raise serializers.ValidationError({
                    "sku":
                    f"Duplicate SKU found: {sku}"
                })

            sku_list.append(sku)

            if ProductVariant.objects.filter(
                sku=sku
            ).exists():

                raise serializers.ValidationError({
                    "sku":
                    f"SKU already exists: {sku}"
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        variants_data = validated_data.pop(
            "variants"
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