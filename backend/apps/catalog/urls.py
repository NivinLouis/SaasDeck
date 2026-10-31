from django.urls import path

from .views import AttributeDetailView, AttributeListCreateView, ProductDetailView, ProductListCreateView, TaxDetailView, TaxListCreateView, VariantDetailView, VariantListCreateView


urlpatterns = [
    path("taxes", TaxListCreateView.as_view(), name="tax-list"),
    path("taxes/<int:pk>", TaxDetailView.as_view(), name="tax-detail"),
    path("attributes", AttributeListCreateView.as_view(), name="attribute-list"),
    path("attributes/<int:pk>", AttributeDetailView.as_view(), name="attribute-detail"),
    path("variants", VariantListCreateView.as_view(), name="variant-list"),
    path("variants/<int:pk>", VariantDetailView.as_view(), name="variant-detail"),
    path("products", ProductListCreateView.as_view(), name="product-list"),
    path("products/<int:pk>", ProductDetailView.as_view(), name="product-detail"),
]
