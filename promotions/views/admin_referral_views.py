from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils.permissions import IsAdminUserCustom
from promotions.models import ReferralProgram
from promotions.referral_serializers import (
    AdminReferralProgramSerializer,
)


class AdminReferralProgramView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
    ):

        program = (
            ReferralProgram.objects.order_by(
                "-id",
            ).first()
        )

        if program is None:

            return Response(
                {
                    "program": None,
                },
            )

        serializer = AdminReferralProgramSerializer(
            program,
        )

        return Response(
            {
                "program": serializer.data,
            },
        )

    def post(
        self,
        request,
    ):

        serializer = AdminReferralProgramSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        program = serializer.save()

        return Response(
            {
                "program": AdminReferralProgramSerializer(
                    program,
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def patch(
        self,
        request,
    ):

        program = (
            ReferralProgram.objects.order_by(
                "-id",
            ).first()
        )

        if program is None:

            serializer = AdminReferralProgramSerializer(
                data=request.data,
            )

            serializer.is_valid(
                raise_exception=True,
            )

            program = serializer.save()

            return Response(
                {
                    "program": AdminReferralProgramSerializer(
                        program,
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        serializer = AdminReferralProgramSerializer(
            program,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        program = serializer.save()

        return Response(
            {
                "program": AdminReferralProgramSerializer(
                    program,
                ).data,
            },
        )
