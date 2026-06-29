import re

from rest_framework import serializers

from accounts.models.address import Address


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address

        fields = [
            "id",
            "name",
            "phone",
            "address_line",
            "city",
            "state",
            "pincode",
            "is_default",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):

        clean = str(value or "").strip()

        if not clean:
            raise serializers.ValidationError(
                "Full name is required",
            )

        return clean

    def validate_phone(self, value):

        clean = str(value or "").strip()

        if not re.match(r"^[6-9]\d{9}$", clean):
            raise serializers.ValidationError(
                "Enter valid 10 digit phone number",
            )

        return clean

    def validate_address_line(self, value):

        clean = str(value or "").strip()

        if not clean:
            raise serializers.ValidationError(
                "Address is required",
            )

        if len(clean) < 10:
            raise serializers.ValidationError(
                "Address should be at least 10 characters",
            )

        return clean

    def validate_city(self, value):

        clean = str(value or "").strip()

        if not clean:
            raise serializers.ValidationError(
                "City is required",
            )

        return clean

    def validate_state(self, value):

        clean = str(value or "").strip()

        if not clean:
            raise serializers.ValidationError(
                "State is required",
            )

        return clean

    def validate_pincode(self, value):

        clean = str(value or "").strip()

        if not re.match(r"^\d{6}$", clean):
            raise serializers.ValidationError(
                "Enter valid 6 digit pincode",
            )

        return clean
