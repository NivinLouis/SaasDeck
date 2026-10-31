from django.urls import path

from .views import (
    ActivateSubscriptionView,
    CancelSubscriptionView,
    PauseSubscriptionView,
    ResumeSubscriptionView,
    QuotationTemplateDetailView,
    QuotationTemplateListCreateView,
    SubscriptionDetailView,
    SubscriptionListCreateView,
)


urlpatterns = [
    path("quotation-templates", QuotationTemplateListCreateView.as_view(), name="quotation-template-list"),
    path("quotation-templates/<uuid:uuid>", QuotationTemplateDetailView.as_view(), name="quotation-template-detail"),
    path("subscriptions", SubscriptionListCreateView.as_view(), name="subscription-list"),
    path("subscriptions/<uuid:uuid>", SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("subscriptions/<uuid:uuid>/activate", ActivateSubscriptionView.as_view(), name="subscription-activate"),
    path("subscriptions/<uuid:uuid>/pause", PauseSubscriptionView.as_view(), name="subscription-pause"),
    path("subscriptions/<uuid:uuid>/resume", ResumeSubscriptionView.as_view(), name="subscription-resume"),
    path("subscriptions/<uuid:uuid>/cancel", CancelSubscriptionView.as_view(), name="subscription-cancel"),
]
