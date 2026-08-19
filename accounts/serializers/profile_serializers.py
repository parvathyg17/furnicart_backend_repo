from datetime import date

from rest_framework import serializers

from accounts.models.profile import UserProfile
from accounts.models.users import User


class OptionalDateField(serializers.DateField):

    def to_internal_value(self, value):

        if value in (None, ""):
            return None

        return super().to_internal_value(value)


class UserProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username", read_only=True)

    email = serializers.EmailField(source="user.email", read_only=True)

    date_of_birth = OptionalDateField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = ["username", "email", "phone", "date_of_birth", "profile_image"]

    def validate_username(self,value):
        return value.title()

    def validate_date_of_birth(self, value):

        if not value:
            return value

        today = date.today()

        if value > today:
            raise serializers.ValidationError("Date of birth cannot be in the future")

        age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )

        if age < 13:
            raise serializers.ValidationError("You must be at least 13 years old")

        return value

    def validate_profile_image(self, value):

        if not value:
            return value

        import os
        ext = os.path.splitext(value.name)[1].lower()
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

        if ext not in valid_extensions:
            raise serializers.ValidationError(
                "Unsupported file extension. Only images (jpg, jpeg, png, webp, gif) are allowed."
            )

        if hasattr(value, "content_type"):
            if not value.content_type.startswith("image/"):
                raise serializers.ValidationError(
                    "Uploaded file is not a valid image."
                )

        return value

    def validate_phone(self, value):

        request = self.context.get("request")

        if not request:
            return value

        user = request.user

        if not value:
            return value

        import re

        clean = str(value).strip()

        if not re.match(r"^[6-9]\d{9}$", clean):
            raise serializers.ValidationError(
                "Phone number must be a valid 10 digit number"
            )

        existing_profile = (
            UserProfile.objects.filter(phone=clean).exclude(user=user).first()
        )

        if existing_profile:

            raise serializers.ValidationError("Phone number already in use")

        return clean


class EmailChangeRequestSerializer(serializers.Serializer):

    new_email = serializers.EmailField()

    def validate_new_email(self, value):

        request = self.context.get("request")

        user = request.user

        if user.email == value:

            raise serializers.ValidationError("This is already your current email")

        if User.objects.filter(email=value).exists():

            raise serializers.ValidationError("This email is already in use")

        return value


class EmailChangeVerifySerializer(serializers.Serializer):

    new_email = serializers.EmailField()

    otp = serializers.CharField(max_length=6)
