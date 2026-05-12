# adminpanel/views.py

from django.contrib.auth import authenticate

from django.core.paginator import Paginator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User

from core.utils.permissions import IsAdminUserCustom

from .throttles import AdminLoginThrottle

from .serializers import AdminLoginSerializer


# ======================================================
# ADMIN LOGIN
# ======================================================

class AdminLoginView(APIView):

    throttle_classes = [AdminLoginThrottle]

    def post(self, request):

        serializer = AdminLoginSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        password = serializer.validated_data["password"]

        user = authenticate(
            email=email,
            password=password
        )

        if not user:

            return Response(
                {"error": "Invalid credentials"},
                status=400
            )

        if not user.is_superuser:

            return Response(
                {"error": "Not authorized"},
                status=403
            )

        if not user.is_active:

            return Response(
                {"error": "Account blocked"},
                status=403
            )

        refresh = RefreshToken.for_user(user)

        response = Response({

            "message": "Admin login successful",

            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_admin": True,
            }
        })

        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        return response


# ======================================================
# USER LIST
# ======================================================

class UserListView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def get(self, request):

        search = request.GET.get("search", "")

        try:
            page = int(request.GET.get("page", 1))

        except ValueError:
            page = 1

        users = User.objects.only(
            "id",
            "email",
            "username",
            "is_active",
            "is_verified",
            "date_joined"
        ).order_by("-id")

        # SEARCH
        if search:

            users = users.filter(
                email__icontains=search
            )

        # PAGINATION
        paginator = Paginator(users, 5)

        page_obj = paginator.get_page(page)

        # RESPONSE DATA
        data = [

            {
                "id": user.id,

                "email": user.email,

                "username": user.username,

                "is_active": user.is_active,

                "is_verified": user.is_verified,

                "status": (
                    "blocked" if not user.is_active
                    else "unverified" if not user.is_verified
                    else "active"
                ),

                "date_joined": user.date_joined
            }

            for user in page_obj
        ]

        return Response({

            "total_pages": paginator.num_pages,

            "current_page": page,

            "users": data
        })


# ======================================================
# BLOCK / UNBLOCK USER
# ======================================================

class BlockUserView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def patch(self, request, user_id):

        try:

            user = User.objects.get(id=user_id)

        except User.DoesNotExist:

            return Response(
                {"error": "User not found"},
                status=404
            )

        # prevent self blocking
        if user == request.user:

            return Response(
                {"error": "Cannot block yourself"},
                status=400
            )

        # prevent blocking other admins
        if user.is_superuser:

            return Response(
                {"error": "Cannot block another admin"},
                status=403
            )

        # toggle active status
        user.is_active = not user.is_active

        user.save()

        return Response({

    "id": user.id,

    "message": (
        "User blocked"
        if not user.is_active
        else "User unblocked"
    ),

    "is_active": user.is_active,

    "status": (
        "blocked" if not user.is_active
        else "unverified" if not user.is_verified
        else "active"
    )
})


# ======================================================
# ADMIN LOGOUT
# ======================================================

class AdminLogoutView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def post(self, request):

        refresh_token = request.COOKIES.get(
            "refresh_token"
        )

        if refresh_token:

            try:

                token = RefreshToken(
                    refresh_token
                )

                token.blacklist()

            except Exception:
                pass

        response = Response({
            "message": "Admin logged out"
        })

        response.delete_cookie("access_token")

        response.delete_cookie("refresh_token")

        return response


# ======================================================
# ADMIN ME
# ======================================================

class AdminMeView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom
    ]

    def get(self, request):

        user = request.user

        return Response({

            "id": user.id,

            "email": user.email,

            "username": user.username,

            "is_admin": user.is_superuser,
        })





















# from django.contrib.auth import authenticate
# from rest_framework.views import APIView
# from rest_framework.response import Response

# from rest_framework_simplejwt.tokens import RefreshToken
# from users.models import User
# from rest_framework.permissions import IsAuthenticated
# from core.utils.permissions import IsAdminUserCustom


# from django.contrib.auth import authenticate
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework_simplejwt.tokens import RefreshToken


# class AdminLoginView(APIView):

#     def post(self, request):
#         email = request.data.get("email")
#         password = request.data.get("password")

#         user = authenticate(username=email, password=password)

#         if not user:
#             return Response({"error": "Invalid credentials"}, status=400)

#         if not user.is_superuser:
#             return Response({"error": "Not authorized"}, status=403)

#         if not user.is_active:
#             return Response({"error": "Account blocked"}, status=403)

#         refresh = RefreshToken.for_user(user)

#         response = Response({
#     "message": "Admin login successful"
# })
#         response.set_cookie(
#             key="access_token",
#             value=str(refresh.access_token),
#             httponly=True,
#             secure=False,
#             samesite="Lax"
# )
#         response.set_cookie(
#             key="refresh_token",
#             value=str(refresh),
#             httponly=True,
#             secure=False,
#             samesite="Lax"
# )
#         return response
    

# from django.core.paginator import Paginator


# class UserListView(APIView):

#     permission_classes = [IsAuthenticated, IsAdminUserCustom]

#     def get(self, request):

#         search = request.GET.get("search", "")
#         page = int(request.GET.get("page", 1))

#         users = User.objects.all().order_by("-id")

#         # SEARCH
#         if search:
#             users = users.filter(email__icontains=search)

#         # PAGINATION
#         paginator = Paginator(users, 5)
#         page_obj = paginator.get_page(page)

#         # RESPONSE DATA
#         data = [
#             {
#                 "id": user.id,
#                 "email": user.email,
#                 "username": user.username,

#                 "is_active": user.is_active,
#                 "is_verified": user.is_verified,

#                 # ✅ FIXED STATUS LOGIC (IMPORTANT)
#                 "status": (
#                     "blocked" if not user.is_active
#                     else "unverified" if not user.is_verified
#                     else "active"
#                 ),

#                 "date_joined": user.date_joined
#             }
#             for user in page_obj
#         ]

#         return Response({
#             "total_pages": paginator.num_pages,
#             "current_page": page,
#             "users": data
#         })
    

# class BlockUserView(APIView):

#     permission_classes = [IsAuthenticated, IsAdminUserCustom]

#     def patch(self, request, user_id):

#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({"error": "User not found"}, status=404)

#         # prevent self-blocking
#         if user == request.user:
#             return Response(
#                 {"error": "Cannot block yourself"},
#                 status=400
#             )

#         # toggle block status
#         user.is_active = not user.is_active
#         user.save()

#         return Response({
#             "message": "User blocked" if not user.is_active else "User unblocked",
#             "is_active": user.is_active,

#             # ✅ ALSO RETURN STATUS FOR UI
#             "status": (
#                 "blocked" if not user.is_active
#                 else "unverified" if not user.is_verified
#                 else "active"
#             )
#         })
    

# class AdminLogoutView(APIView):
    

#     def post(self, request):
#         response = Response({"message": "Admin logged out"})

#         response.delete_cookie("access_token")
#         response.delete_cookie("refresh_token")

#         return response


# class AdminMeView(APIView):

    
#     permission_classes = [IsAuthenticated, IsAdminUserCustom]

#     def get(self, request):

#         user = request.user

#         return Response({
#             "id": user.id,
#             "email": user.email,
#             "username": user.username,
#             "is_admin": user.is_superuser,
#         })