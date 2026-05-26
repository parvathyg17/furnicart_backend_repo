from rest_framework import serializers

from PIL import Image

from catalog.models import Category


class CategoryChildSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = Category

        fields = [
            "id",
            "name",
            "slug",
            "image",
            "is_active",
        ]


class CategorySerializer(
    serializers.ModelSerializer
):

    parent_name = serializers.CharField(
        source="parent.name",
        read_only=True
    )

    children = serializers.SerializerMethodField()

    children_count = serializers.SerializerMethodField()

    image_url = serializers.SerializerMethodField()

    class Meta:

        model = Category

        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "parent_name",
            "children",
            "children_count",
            "description",
            "image",
            "image_url",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
            "is_active",
        ]

    # ==========================================
    # GLOBAL VALIDATION
    # ==========================================

    def validate(self, attrs):

        # IMAGE REQUIRED ONLY ON CREATE

        if (
            not self.instance
            and
            not attrs.get("image")
        ):

            raise serializers.ValidationError({
                "image":
                "Category image is required"
            })

        return attrs

    # ==========================================
    # VALIDATE NAME
    # ==========================================

    def validate_name(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError(
                "Category name is required"
            )

        if len(value) < 4:

            raise serializers.ValidationError(
                "Category name must be at least 4 characters"
            )

        return value

    # ==========================================
    # VALIDATE DESCRIPTION
    # ==========================================

    def validate_description(self, value):

        value = value.strip()

        if not value:

            raise serializers.ValidationError(
                "Description is required"
            )

        if len(value) < 10:

            raise serializers.ValidationError(
                "Description must be at least 10 characters"
            )

        return value

    # ==========================================
    # VALIDATE IMAGE
    # ==========================================

    def validate_image(self, value):

        if value:

            # ==========================================
            # FILE SIZE
            # ==========================================

            if (
                value.size >
                5 * 1024 * 1024
            ):

                raise serializers.ValidationError(
                    "Image size must be below 5MB"
                )

            # ==========================================
            # FILE TYPE
            # ==========================================

            valid_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            if (
                hasattr(value, "content_type")
                and
                value.content_type not in valid_types
            ):

                raise serializers.ValidationError(
                    "Only JPEG, PNG and WEBP images are allowed"
                )

            # ==========================================
            # VERIFY REAL IMAGE
            # ==========================================

            try:

                image = Image.open(value)

                image.verify()

            except Exception:

                raise serializers.ValidationError(
                    "Invalid or corrupted image file"
                )

            # RESET FILE POINTER

            value.seek(0)

            # ==========================================
            # IMAGE DIMENSIONS
            # ==========================================

            image = Image.open(value)

            width, height = image.size

            # MIN SIZE

            if (
                width < 300
                or
                height < 300
            ):

                raise serializers.ValidationError(
                    "Image must be at least 300x300 pixels"
                )

            # MAX SIZE

            if (
                width > 5000
                or
                height > 5000
            ):

                raise serializers.ValidationError(
                    "Image dimensions too large"
                )

            # RESET AGAIN

            value.seek(0)

        return value

    # ==========================================
    # VALIDATE PARENT
    # ==========================================

    def validate_parent(self, value):

        # OPTIONAL PARENT

        if not value:

            return value

        # SELF PARENT CHECK

        if (
            self.instance
            and
            value == self.instance
        ):

            raise serializers.ValidationError(
                "Category cannot be parent of itself"
            )

        # CIRCULAR LOOP CHECK

        parent = value

        while parent:

            if (
                self.instance
                and
                parent == self.instance
            ):

                raise serializers.ValidationError(
                    "Circular category hierarchy detected"
                )

            parent = parent.parent

        return value

    # ==========================================
    # CHILDREN
    # ==========================================

    def get_children(self, obj):

        request = self.context.get(
            "request"
        )

        # ADMIN

        if (
            request
            and
            request.path.startswith(
                "/api/admin/"
            )
        ):

            children = obj.children.all()

        # USER

        else:

            children = obj.children.filter(
                is_active=True
            )

        serializer = CategoryChildSerializer(
            children,
            many=True,
            context=self.context
        )

        return serializer.data

    # ==========================================
    # CHILDREN COUNT
    # ==========================================

    def get_children_count(self, obj):

        return obj.children.count()

    # ==========================================
    # IMAGE URL
    # ==========================================

    def get_image_url(self, obj):

        request = self.context.get(
            "request"
        )

        if obj.image and request:

            return request.build_absolute_uri(
                obj.image.url
            )

        return None