"""Plan catalog endpoints."""
from django.db.models import Q
from django.utils.timezone import localdate
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.core.permissions import IsStaffOrAdmin

from .models import PaymentTerm, Plan
from .serializers import PaymentTermSerializer, PlanSerializer


class PaymentTermListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentTermSerializer
    permission_classes = [IsStaffOrAdmin]
    queryset = PaymentTerm.objects.all()


class PaymentTermDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PaymentTermSerializer
    permission_classes = [IsStaffOrAdmin]
    queryset = PaymentTerm.objects.all()


class PlanListCreateView(generics.ListCreateAPIView):
    serializer_class = PlanSerializer
    filterset_fields = ("product", "billing_interval", "currency", "is_active")
    search_fields = ("name", "code", "description")
    ordering_fields = ("name", "price", "created_at", "updated_at")
    ordering = ("name",)

    def get_queryset(self):
        queryset = Plan.objects.select_related("product", "payment_term").all()
        if self.request.user.role == "customer":
            today = localdate()
            return queryset.filter(
                is_active=True,
                is_public=True,
                product__is_active=True,
            ).filter(
                Q(available_from__isnull=True) | Q(available_from__lte=today),
                Q(available_until__isnull=True) | Q(available_until__gte=today),
            )
        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaffOrAdmin()]
        return super().get_permissions()


class PlanDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PlanSerializer

    def get_queryset(self):
        queryset = Plan.objects.select_related("product", "payment_term").all()
        if self.request.user.role == "customer":
            today = localdate()
            return queryset.filter(
                is_active=True,
                product__is_active=True,
            ).filter(
                Q(available_from__isnull=True) | Q(available_from__lte=today),
                Q(available_until__isnull=True) | Q(available_until__gte=today),
            )
        return queryset

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH"}:
            return [IsStaffOrAdmin()]
        return super().get_permissions()


class PublicPlanShowcaseView(generics.ListAPIView):
    """Unauthenticated plan catalogue; a customer account is required to request a quote."""

    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        today = localdate()
        return Plan.objects.select_related("product", "payment_term").filter(
            is_active=True,
            is_public=True,
            product__is_active=True,
        ).filter(
            Q(available_from__isnull=True) | Q(available_from__lte=today),
            Q(available_until__isnull=True) | Q(available_until__gte=today),
        ).order_by("price")
