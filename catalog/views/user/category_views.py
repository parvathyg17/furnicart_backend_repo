from rest_framework.views import APIView
from rest_framework.response import Response

from catalog.selectors.category_selectors import (
    get_user_filtered_categories
)

from catalog.serializers.category_serializers import (
    CategorySerializer
)


class UserCategoryListView(APIView):

    permission_classes = []

    def get(self, request):

        categories = get_user_filtered_categories(
            request.GET
        )

        serializer = CategorySerializer(
            categories,
            many=True,
            context={
                "request": request
            }
        )

        return Response(
            serializer.data
        )