from rest_framework.views import APIView
from rest_framework.response import Response

from core.utils.jwt import get_tokens_for_user
from adminpanel.services import admin_login_service


class AdminLoginView(APIView):
    def post(self, request):

        user, error = admin_login_service(
            request.data.get("email"),
            request.data.get("password")
        )

        if error:
            return Response({"error": error}, status=400)

        tokens = get_tokens_for_user(user)

        return Response({
            "tokens": tokens,
            "admin": {
                "id": user.id,
                "email": user.email
            }
        })