from rest_framework import generics
from rest_framework.exceptions import NotFound
from apps.core.permissions import IsCustomer, IsStaffOrAdmin
from .models import Customer
from .serializers import CustomerSerializer


class CustomerListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsStaffOrAdmin]
    filterset_fields = ["city", "country"]
    search_fields = ["name", "company", "email", "phone"]
    ordering_fields = ["name", "created_at"]
    queryset = Customer.objects.select_related("user", "created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CustomerDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsStaffOrAdmin]
    queryset = Customer.objects.select_related("user", "created_by")


class PortalProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsCustomer]

    def get_object(self):
        try:
            return self.request.user.customer_profile
        except Customer.DoesNotExist as exc:
            raise NotFound("Customer profile not found.") from exc
