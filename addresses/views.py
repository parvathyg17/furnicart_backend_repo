from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound

from .models import Address
from .serializers import AddressSerializer
from .services import set_default_address

class AddressView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = Address.objects.filter(
            user=request.user,
            is_deleted=False
        )
        return Response(AddressSerializer(addresses, many=True).data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_default = serializer.validated_data.get("is_default", False)

        address = serializer.save(
            user=request.user,
            is_default=False
        )

        has_other = Address.objects.filter(
            user=request.user,
            is_deleted=False
        ).exclude(id=address.id).exists()

        if not has_other or is_default:
            set_default_address(request.user, address)

        return Response(AddressSerializer(address).data, status=201)
    


class AddressDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return Address.objects.get(
                id=pk,
                user=request.user,
                is_deleted=False
            )
        except Address.DoesNotExist:
            raise NotFound("Address not found")

    def get(self, request, pk):
        address = self.get_object(request, pk)
        return Response(AddressSerializer(address).data)

    def put(self, request, pk):
        address = self.get_object(request, pk)

        serializer = AddressSerializer(
            address,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        is_default = serializer.validated_data.get("is_default", False)

        address = serializer.save()

        if is_default:
            set_default_address(request.user, address)

        return Response(AddressSerializer(address).data)

    def delete(self, request, pk):
        address = self.get_object(request, pk)

        if address.is_default:
            next_address = Address.objects.filter(
                user=request.user,
                is_deleted=False
            ).exclude(id=address.id).first()

            if next_address:
                set_default_address(request.user, next_address)

        address.is_deleted = True
        address.is_default = False
        address.save()

        return Response({"message": "Deleted"})


class SetDefaultAddressView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        address = Address.objects.get(
            id=pk,
            user=request.user,
            is_deleted=False
        )

        set_default_address(request.user, address)

        return Response({"message": "Default updated"})