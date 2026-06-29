from decimal import Decimal

from rest_framework import serializers

from promotions.models import Coupon, ReferralProgram


class ReferralMeSerializer(
    serializers.Serializer,
):

    program_active = serializers.BooleanField()

    referral_code = serializers.CharField(
        allow_blank=True,
    )

    referral_token = serializers.CharField(
        allow_blank=True,
    )

    referee_benefit = serializers.CharField(
        allow_blank=True,
    )

    referrer_reward_amount = serializers.CharField(
        allow_blank=True,
    )

    welcome_coupon = serializers.DictField(
        allow_null=True,
    )


class AdminReferralProgramSerializer(
    serializers.ModelSerializer,
):

    class Meta:

        model = ReferralProgram

        fields = [
            "id",
            "name",
            "is_active",
            "referee_discount_type",
            "referee_discount_value",
            "referee_max_discount_amount",
            "referee_coupon_valid_days",
            "referrer_reward_amount",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_referee_discount_value(
        self,
        value,
    ):

        discount_type = (
            self.initial_data.get(
                "referee_discount_type",
            )
            or (
                self.instance.referee_discount_type
                if self.instance
                else Coupon.DiscountType.PERCENT
            )
        )

        value = Decimal(
            str(
                value,
            ),
        )

        if discount_type == Coupon.DiscountType.PERCENT:

            if value <= Decimal(
                "0",
            ) or value > Decimal(
                "100",
            ):

                raise serializers.ValidationError(
                    "Percentage must be between 0 and 100.",
                )

        elif value <= Decimal(
            "0",
        ):

            raise serializers.ValidationError(
                "Fixed discount must be greater than 0.",
            )

        return value
