from django.urls import path

from .views import (
    ActivateSubscriptionView,
    CancelSubscriptionView,
    ConfirmSubscriptionView,
    CustomerAcceptQuotationView,
    CustomerCancelSubscriptionView,
    CustomerPauseSubscriptionView,
    CustomerPlanRequestView,
    CustomerResumeSubscriptionView,
    CreateQuotationFromTemplateView,
    PauseSubscriptionView,
    QuotationTemplateDetailView,
    QuotationTemplateListCreateView,
    ResumeSubscriptionView,
    SendQuotationView,
    SubscriptionDetailView,
    SubscriptionLifecycleRunView,
    SubscriptionListCreateView,
)


urlpatterns = [
    path("quotation-templates", QuotationTemplateListCreateView.as_view(), name="quotation-template-list"),
    path("quotation-templates/<uuid:uuid>", QuotationTemplateDetailView.as_view(), name="quotation-template-detail"),
    path("quotation-templates/<uuid:uuid>/quotations", CreateQuotationFromTemplateView.as_view(), name="quotation-template-create-quotation"),
    path("subscriptions", SubscriptionListCreateView.as_view(), name="subscription-list"),
    path("subscriptions/<uuid:uuid>", SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("subscriptions/<uuid:uuid>/send-quotation", SendQuotationView.as_view(), name="subscription-send-quotation"),
    path("subscriptions/<uuid:uuid>/confirm", ConfirmSubscriptionView.as_view(), name="subscription-confirm"),
    path("subscriptions/<uuid:uuid>/activate", ActivateSubscriptionView.as_view(), name="subscription-activate"),
    path("subscriptions/<uuid:uuid>/pause", PauseSubscriptionView.as_view(), name="subscription-pause"),
    path("subscriptions/<uuid:uuid>/resume", ResumeSubscriptionView.as_view(), name="subscription-resume"),
    path("subscriptions/<uuid:uuid>/cancel", CancelSubscriptionView.as_view(), name="subscription-cancel"),
    path("subscriptions/lifecycle/run", SubscriptionLifecycleRunView.as_view(), name="subscription-lifecycle-run"),
    path("portal/subscriptions/<uuid:uuid>/accept", CustomerAcceptQuotationView.as_view(), name="portal-subscription-accept"),
    path("portal/subscriptions/<uuid:uuid>/pause", CustomerPauseSubscriptionView.as_view(), name="portal-subscription-pause"),
    path("portal/subscriptions/<uuid:uuid>/resume", CustomerResumeSubscriptionView.as_view(), name="portal-subscription-resume"),
    path("portal/subscriptions/<uuid:uuid>/cancel", CustomerCancelSubscriptionView.as_view(), name="portal-subscription-cancel"),
    path("portal/plan-requests", CustomerPlanRequestView.as_view(), name="portal-plan-request"),
]
