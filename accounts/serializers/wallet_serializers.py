from rest_framework import serializers

from accounts.models.wallet import Wallet, WalletTransaction


class WalletSerializer(
    serializers.ModelSerializer,
):

    class Meta:

        model = Wallet

        fields = [
            "balance",
            "updated_at",
        ]


class WalletTransactionSerializer(
    serializers.ModelSerializer,
):

    order_number = serializers.CharField(
        source="order.order_number",
        read_only=True,
        default=None,
    )

    reason_display = serializers.CharField(
        source="get_reason_display",
        read_only=True,
    )

    type_display = serializers.CharField(
        source="get_type_display",
        read_only=True,
    )

    class Meta:

        model = WalletTransaction

        fields = [
            "id",
            "type",
            "type_display",
            "amount",
            "reason",
            "reason_display",
            "order_number",
            "reference_note",
            "balance_after",
            "created_at",
        ]
