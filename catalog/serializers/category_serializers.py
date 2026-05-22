from rest_framework import serializers

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

    class Meta:

        model = Category

        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "parent_name",
            "children",
            "description",
            "image",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]

    # ==========================================
    # VALIDATE NAME
    # ==========================================

    def validate_name(self, value):

        value = value.strip()

        if len(value) < 2:

            raise serializers.ValidationError(
                "Category name too short"
            )

        return value

    # ==========================================
    # CHILDREN
    # ==========================================

    def get_children(self, obj):

        request = self.context.get(
            "request"
        )

        # ==========================================
        # ADMIN
        # ==========================================

        if (
            request
            and
            request.path.startswith(
                "/api/admin/"
            )
        ):

            children = obj.children.all()

        # ==========================================
        # USER
        # ==========================================

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
    # VALIDATE PARENT
    # ==========================================

    def validate_parent(self, value):

        # SELF PARENT CHECK

        if self.instance and value == self.instance:

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