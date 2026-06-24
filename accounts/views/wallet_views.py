from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.wallet import WalletTransaction
from accounts.serializers.wallet_serializers import (
    WalletSerializer,
    WalletTransactionSerializer,
)
from accounts.services.wallet_services import (
    ensure_wallet,
)
from core.pagination import CustomPagination


class WalletView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
    ):

        wallet = ensure_wallet(
            request.user,
        )

        serializer = WalletSerializer(
            wallet,
        )

        return Response(
            serializer.data,
        )


class WalletTransactionListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
    ):

        wallet = ensure_wallet(
            request.user,
        )

        queryset = (
            WalletTransaction.objects.filter(
                wallet=wallet,
            )
            .select_related(
                "order",
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

        txn_type = (
            request.query_params.get(
                "type",
                "",
            )
            or ""
        ).strip()

        if txn_type in (
            WalletTransaction.Type.CREDIT,
            WalletTransaction.Type.DEBIT,
        ):

            queryset = queryset.filter(
                type=txn_type,
            )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        serializer = WalletTransactionSerializer(
            page,
            many=True,
        )

        if page is not None:

            return paginator.get_paginated_response(
                serializer.data,
            )

        return Response(
            serializer.data,
        )
