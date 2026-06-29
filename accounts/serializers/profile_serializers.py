from rest_framework import serializers
from accounts.models.profile import UserProfile
from accounts.models.users import User


class UserProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'email',
            'phone',
            'date_of_birth',
            'profile_image'
        ]

    def validate_phone(
        self,
        value
    ):

        request = self.context.get(
            "request"
        )

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

        existing_profile = UserProfile.objects.filter(
            phone=clean
        ).exclude(
            user=user
        ).first()

        if existing_profile:

            raise serializers.ValidationError(
                "Phone number already in use"
            )

        return clean


class EmailChangeRequestSerializer(serializers.Serializer):

    new_email = serializers.EmailField()

    def validate_new_email(
        self,
        value
    ):

        request = self.context.get(
            "request"
        )

        user = request.user

        if user.email == value:

            raise serializers.ValidationError(
                "This is already your current email"
            )

        if User.objects.filter(
            email=value
        ).exists():

            raise serializers.ValidationError(
                "This email is already in use"
            )

        return value


class EmailChangeVerifySerializer(serializers.Serializer):

    new_email = serializers.EmailField()

    otp = serializers.CharField(
        max_length=6
    )