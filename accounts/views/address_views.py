from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models.address import Address
from accounts.serializers.address_serializers import AddressSerializer
from accounts.services.address_services import set_default_address


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Address.objects.filter(
            user=self.request.user,
            is_deleted=False,
        )

    def perform_create(self, serializer):
        is_default = serializer.validated_data.get("is_default", False)
        address = serializer.save(user=self.request.user, is_default=False)
        has_other = (
            Address.objects.filter(user=self.request.user, is_deleted=False)
            .exclude(id=address.id)
            .exists()
        )
        if not has_other or is_default:
            set_default_address(self.request.user, address)

    def perform_update(self, serializer):
        wants_default = serializer.validated_data.pop("is_default", False)
        address = serializer.save()
        if wants_default:
            set_default_address(self.request.user, address)

    def perform_destroy(self, instance):
        if instance.is_default:
            next_address = (
                Address.objects.filter(
                    user=self.request.user,
                    is_deleted=False,
                )
                .exclude(id=instance.id)
                .first()
            )
            if next_address:
                set_default_address(self.request.user, next_address)
        instance.is_deleted = True
        instance.is_default = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Deleted"})

    @action(detail=True, methods=["patch"], url_path="set-default")
    def set_default(self, request, pk=None):
        address = self.get_object()
        set_default_address(request.user, address)
        return Response({"message": "Default updated"})
