from rest_framework import generics, permissions, status,filters
from rest_framework.response import Response
from accounts.models.contact import ContactMessage
from accounts.serializers.contact_serializers import ContactMessageSerializer
from core.pagination import CustomPagination

class PublicContactMessageView(generics.CreateAPIView):
    
    
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        message_text = serializer.validated_data.get('message', '').lower()
        subject_text = serializer.validated_data.get('subject', '').lower()
        combined_text = f"{subject_text} {message_text}"
        
        if any(keyword in combined_text for keyword in ['delivery', 'shipping']):
            reply = "Thank you for reaching out! Our standard delivery time is 3-5 business days. You can track your order in your profile."
        elif any(keyword in combined_text for keyword in ['return', 'exchange']):
            reply = "Thank you for reaching out! You can return items within 30 days of delivery. Please visit our Returns page for instructions."
        elif 'refund' in combined_text:
            reply = "Thank you for reaching out! Refunds are processed within 5-7 business days after we receive the returned item."
        else:
            reply = "Thank you for reaching out! The admin will contact you through email shortly. Please wait."
            
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": reply, "data": serializer.data}, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )


class AdminContactMessageListView(generics.ListAPIView):
    
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "email", "subject", "message"]


class AdminContactMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAdminUser]
