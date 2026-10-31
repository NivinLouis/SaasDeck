from django.urls import path

from .views import PaymentDetailView, PaymentListCreateView, PaymentRefundView


urlpatterns = [
    path("payments", PaymentListCreateView.as_view(), name="payment-list"),
    path("payments/<uuid:uuid>", PaymentDetailView.as_view(), name="payment-detail"),
    path("payments/<uuid:uuid>/refund", PaymentRefundView.as_view(), name="payment-refund"),
]
