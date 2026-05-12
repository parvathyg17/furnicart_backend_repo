# adminpanel/serializers.py

from rest_framework import serializers


class AdminLoginSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField()