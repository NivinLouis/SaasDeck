from django.urls import path

from .views import ProductDetailView, ProductListCreateView, TaxDetailView, TaxListCreateView


urlpatterns = [
    path("taxes", TaxListCreateView.as_view(), name="tax-list"),
    path("taxes/<int:pk>", TaxDetailView.as_view(), name="tax-detail"),
    path("products", ProductListCreateView.as_view(), name="product-list"),
    path("products/<int:pk>", ProductDetailView.as_view(), name="product-detail"),
]
