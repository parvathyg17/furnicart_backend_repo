from rest_framework import serializers
from .models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password


from rest_framework import serializers

from django.contrib.auth.password_validation import (
    validate_password
)

from .models import User

import re


class SignupSerializer(
    serializers.ModelSerializer
):

    password = serializers.CharField(
        write_only=True
    )

    class Meta:

        model = User

        fields = [
            'username',
            'email',
            'password'
        ]


    def validate_username(
        self,
        value
    ):

        username =value.strip()

        # MIN LENGTH

        if len(username) < 3:

            raise serializers.ValidationError(
                "Username must be at least 3 characters"
            )

       

        if len(username) > 20:

            raise serializers.ValidationError(
                "Username cannot exceed 20 characters"
            )

        

        if not re.match(
            r'^[A-Za-z0-9]+$',
            username
        ):

            raise serializers.ValidationError(
                "Username can contain only letters and numbers"
            )

        

        if username.isdigit():

            raise serializers.ValidationError(
                "Username cannot contain only numbers"
            )

        

        blocked_usernames = [
            "admin",
            "administrator",
            "root",
            "superuser",
            "staff",
            "support",
            "owner",
            "furnicart"
        ]

        if username.lower() in blocked_usernames:

            raise serializers.ValidationError(
                "This username is not allowed"
            )

       

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise serializers.ValidationError(
                "Username already exists"
            )

        return username

    

    def validate_email(self, value):
        email = value.lower().strip()
        existing_user = User.objects.filter(
            email__iexact=email).first()
        if existing_user and existing_user.is_verified:
            raise serializers.ValidationError(
                "Email already exists"
                )
        return email



    def validate_password(
        self,
        value
    ):

       

        validate_password(value)

        

        if len(value) < 8:

            raise serializers.ValidationError(
                "Password must be at least 8 characters"
            )

       

        if not re.search(
            r'[A-Z]',
            value
        ):

            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter"
            )

        

        if not re.search(
            r'[a-z]',
            value
        ):

            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter"
            )

        

        if not re.search(
            r'[0-9]',
            value
        ):

            raise serializers.ValidationError(
                "Password must contain at least one number"
            )

        return value

 

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            )
        user.is_verified = False
        user.is_active = True
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    purpose = serializers.CharField()


class ResendOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    purpose = serializers.CharField(
        required=False,
        default="signup"
    )




class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)   
        return value
    
class ChangeEmailRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField()


class VerifyEmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)



class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value