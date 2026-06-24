import logging

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom
from promotions.models import Offer
from promotions.selectors.admin_offer_selectors import (
    get_admin_filtered_offers,
)
from promotions.serializers import AdminOfferSerializer
from promotions.services.admin_offer_services import (
    delete_offer,
)

logger = logging.getLogger(__name__)


class AdminOfferListCreateView(APIView):

    """
    GET: paginated offer list (search, is_active, offer_type).
    POST: create offer.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
    ):

        queryset = get_admin_filtered_offers(
            request.query_params,
        )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        if page is not None:

            serializer = AdminOfferSerializer(
                page,
                many=True,
                context={
                    "request": request,
                },
            )

            logger.info(
                "Admin fetched offers list",
            )

            return paginator.get_paginated_response(
                serializer.data,
            )

        serializer = AdminOfferSerializer(
            queryset,
            many=True,
            context={
                "request": request,
            },
        )

        logger.info(
            "Admin fetched offers list",
        )

        return Response(
            serializer.data,
        )

    def post(
        self,
        request,
    ):

        serializer = AdminOfferSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        logger.info(
            "Admin created offer %s",
            serializer.instance.id,
        )

        return Response(
            {
                "success": True,
                "message": "Offer created successfully",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminOfferDetailView(APIView):

    """
    GET: single offer.
    PATCH: partial update.
    DELETE: remove offer.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
        offer_id,
    ):

        try:

            instance = (
                Offer.objects.select_related(
                    "product",
                    "category",
                ).get(
                    pk=offer_id,
                )
            )

        except Offer.DoesNotExist:

            raise NotFound(
                detail="Offer not found.",
            )

        serializer = AdminOfferSerializer(
            instance,
            context={
                "request": request,
            },
        )

        logger.info(
            "Admin fetched offer %s",
            instance.id,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request,
        offer_id,
    ):

        try:

            instance = Offer.objects.get(
                pk=offer_id,
            )

        except Offer.DoesNotExist:

            raise NotFound(
                detail="Offer not found.",
            )

        serializer = AdminOfferSerializer(
            instance,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        logger.info(
            "Admin updated offer %s",
            instance.id,
        )

        return Response(
            {
                "success": True,
                "message": "Offer updated successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def put(
        self,
        request,
        offer_id,
    ):

        return self.patch(
            request,
            offer_id,
        )

    def delete(
        self,
        request,
        offer_id,
    ):

        try:

            instance = Offer.objects.get(
                pk=offer_id,
            )

        except Offer.DoesNotExist:

            raise NotFound(
                detail="Offer not found.",
            )

        pk = delete_offer(
            instance,
        )

        logger.info(
            "Admin deleted offer %s",
            pk,
        )

        return Response(
            {
                "success": True,
                "message": "Offer deleted successfully",
                "offer_id": pk,
            },
            status=status.HTTP_200_OK,
        )
