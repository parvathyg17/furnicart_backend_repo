from decimal import Decimal

from rest_framework import serializers

from promotions.models import Coupon

from promotions.services.admin_coupon_services import (
    create_coupon,
    update_coupon,
)


class AdminCouponSerializer(
    serializers.ModelSerializer,
):

    class Meta:

        model = Coupon

        fields = [
            "id",
            "code",
            "description",
            "discount_type",
            "discount_value",
            "min_order_subtotal",
            "max_discount_amount",
            "valid_from",
            "valid_until",
            "max_redemptions_total",
            "max_redemptions_per_user",
            "times_used",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "times_used",
            "created_at",
            "updated_at",
        ]

    def validate_code(
        self,
        value,
    ):

        clean = (
            str(
                value,
            )
            .strip()
            .upper()
        )

        if not clean:

            raise serializers.ValidationError(
                "Code cannot be empty.",
            )

        qs = Coupon.objects.filter(
            code=clean,
        )

        if self.instance:

            qs = qs.exclude(
                pk=self.instance.pk,
            )

        if qs.exists():

            raise serializers.ValidationError(
                "A coupon with this code already exists.",
            )

        return clean

    def validate(
        self,
        attrs,
    ):

        valid_from = attrs.get(
            "valid_from",
        )

        valid_until = attrs.get(
            "valid_until",
        )

        if self.instance:

            if valid_from is None:

                valid_from = self.instance.valid_from

            if valid_until is None:

                valid_until = self.instance.valid_until

        if valid_from and valid_until and valid_until <= valid_from:

            raise serializers.ValidationError(
                {
                    "valid_until": "Must be after valid_from.",
                },
            )

        discount_type = attrs.get(
            "discount_type",
        )

        if self.instance and discount_type is None:

            discount_type = self.instance.discount_type

        discount_value = attrs.get(
            "discount_value",
        )

        if self.instance and discount_value is None:

            discount_value = self.instance.discount_value

        if discount_type == Coupon.DiscountType.PERCENT:

            if (
                discount_value is not None
                and (
                    discount_value <= Decimal("0")
                    or discount_value > Decimal("100")
                )
            ):

                raise serializers.ValidationError(
                    {
                        "discount_value": (
                            "Percentage must be greater than 0 and at most 100."
                        ),
                    },
                )

        elif discount_type == Coupon.DiscountType.FIXED:

            if (
                discount_value is not None
                and discount_value <= Decimal("0")
            ):

                raise serializers.ValidationError(
                    {
                        "discount_value": (
                            "Fixed amount must be greater than 0."
                        ),
                    },
                )

        return attrs

    def create(
        self,
        validated_data,
    ):

        return create_coupon(
            validated_data,
        )

    def update(
        self,
        instance,
        validated_data,
    ):

        return update_coupon(
            instance,
            validated_data,
        )
