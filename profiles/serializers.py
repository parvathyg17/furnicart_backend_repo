from rest_framework import serializers
from .models import UserProfile
from users.models import User

class UserProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

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

        request =self.context.get(
                "request"
            )

        user =request.user

        

        if not value:
            return value

       

        if (
            not value.isdigit()
            or
            len(value) != 10
        ):

            raise serializers.ValidationError(
                "Phone number must be 10 digits"
            )

       

        existing_profile =UserProfile.objects.filter(
                phone=value
            ).exclude(
                user=user
            ).first()

        if existing_profile:

            raise serializers.ValidationError(
                "Phone number already in use"
            )

        return value

        








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