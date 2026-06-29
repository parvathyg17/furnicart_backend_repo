from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from promotions.referral_serializers import (
    ReferralMeSerializer,
)
from promotions.services.referral_services import (
    get_active_referral_program,
    get_or_create_referral_code,
    referee_welcome_coupon_payload,
    referral_program_summary,
)


class ReferralMeView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):

        program = get_active_referral_program()

        if program is None:

            payload = {
                "program_active": False,
                "referral_code": "",
                "referral_token": "",
                "referee_benefit": "",
                "referrer_reward_amount": "",
                "welcome_coupon": None,
            }

        else:

            referral_code = get_or_create_referral_code(
                request.user,
            )

            summary = referral_program_summary(
                program,
            )

            payload = {
                "program_active": True,
                "referral_code": referral_code.code,
                "referral_token": referral_code.token,
                "referee_benefit": summary[
                    "referee_benefit"
                ],
                "referrer_reward_amount": summary[
                    "referrer_reward_amount"
                ],
                "welcome_coupon": referee_welcome_coupon_payload(
                    request.user,
                ),
            }

        serializer = ReferralMeSerializer(
            payload,
        )

        return Response(
            serializer.data,
        )
