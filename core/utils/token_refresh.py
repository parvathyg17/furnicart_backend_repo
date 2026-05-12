from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenRefreshSerializer


class CookieTokenRefreshView(TokenRefreshView):

    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):

        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"error": "No refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(
            data={"refresh": refresh_token}
        )

        try:
            serializer.is_valid(raise_exception=True)

        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        access_token = serializer.validated_data["access"]
        new_refresh_token = serializer.validated_data.get("refresh")
        response = Response({
            "message": "Token refreshed"
            })
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="Lax"
            )
        if new_refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=False,
                samesite="Lax"
                )
        return response