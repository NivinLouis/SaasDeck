"""Catalog HTTP endpoints."""
from rest_framework import generics

from apps.core.permissions import IsStaffOrAdmin

from .models import Product, Tax
from .serializers import ProductSerializer, TaxSerializer


class TaxListCreateView(generics.ListCreateAPIView):
    serializer_class = TaxSerializer
    filterset_fields = ("is_active", "is_inclusive")
    search_fields = ("name",)
    ordering_fields = ("name", "rate", "created_at")
    ordering = ("name",)

    def get_queryset(self):
        queryset = Tax.objects.all()
        return queryset.filter(is_active=True) if self.request.user.role == "customer" else queryset

    def get_permissions(self):
        return [IsStaffOrAdmin()] if self.request.method == "POST" else super().get_permissions()


class TaxDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = TaxSerializer

    def get_queryset(self):
        queryset = Tax.objects.all()
        return queryset.filter(is_active=True) if self.request.user.role == "customer" else queryset

    def get_permissions(self):
        return [IsStaffOrAdmin()] if self.request.method in {"PUT", "PATCH"} else super().get_permissions()


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filterset_fields = ("product_type", "is_active")
    search_fields = ("name", "sku", "description")
    ordering_fields = ("name", "sales_price", "created_at", "updated_at")
    ordering = ("name",)

    def get_queryset(self):
        queryset = Product.objects.prefetch_related("product_taxes__tax").all()
        # Customers may only browse products currently available for sale.
        if self.request.user.role == "customer":
            return queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaffOrAdmin()]
        return super().get_permissions()


class ProductDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.prefetch_related("product_taxes__tax").all()
        if self.request.user.role == "customer":
            return queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH"}:
            return [IsStaffOrAdmin()]
        return super().get_permissions()
