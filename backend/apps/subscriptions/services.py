"""Subscription construction, billing-period calculation, and lifecycle transitions."""
from calendar import monthrange
from datetime import timedelta
from uuid import uuid4

from django.db import transaction
from django.utils.timezone import localdate, now
from rest_framework.exceptions import ValidationError

from .models import Subscription


def add_billing_interval(start_date, plan):
    """Return the first date of the following billing period without external dependencies."""
    count = plan.interval_count
    if plan.billing_interval == plan.BillingInterval.DAILY:
        return start_date + timedelta(days=count)
    if plan.billing_interval == plan.BillingInterval.WEEKLY:
        return start_date + timedelta(weeks=count)

    months = count if plan.billing_interval == plan.BillingInterval.MONTHLY else 12 * count
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1
    return start_date.replace(day=min(start_date.day, monthrange(year, month)[1]), year=year, month=month)


def subscription_number():
    """Collision-resistant public reference; UUID avoids a race-prone count-based sequence."""
    return f"SUB-{localdate():%Y}-{uuid4().hex[:8].upper()}"


def validate_plan_for_subscription(plan):
    if not plan.is_active:
        raise ValidationError({"plan": "Archived plans cannot be used for new subscriptions."})
    if plan.product_id and not plan.product.is_active:
        raise ValidationError({"plan": "The product linked to this plan is archived."})


@transaction.atomic
def create_subscription(*, customer, plan, created_by, start_date=None, expiry_date=None, auto_renew=None):
    validate_plan_for_subscription(plan)
    start_date = start_date or localdate()
    next_period_start = add_billing_interval(start_date, plan)
    payment_terms = plan.payment_term.name if plan.payment_term else "Immediate Payment"

    return Subscription.objects.create(
        subscription_number=subscription_number(),
        customer=customer,
        plan=plan,
        status=Subscription.Status.DRAFT,
        start_date=start_date,
        expiry_date=expiry_date,
        current_period_start=start_date,
        current_period_end=next_period_start - timedelta(days=1),
        next_billing_date=next_period_start,
        payment_terms=payment_terms,
        auto_renew=plan.allow_auto_renewal if auto_renew is None else auto_renew,
        created_by=created_by,
    )


@transaction.atomic
def transition_subscription(*, subscription_id, action, cancellation_reason=""):
    subscription = Subscription.objects.select_for_update().select_related("plan").get(pk=subscription_id)
    current = subscription.status

    if action == "activate":
        if current not in {Subscription.Status.DRAFT, Subscription.Status.CONFIRMED, Subscription.Status.TRIAL}:
            raise ValidationError({"status": f"Cannot activate a subscription in {current} state."})
        subscription.status = (
            Subscription.Status.TRIAL
            if current != Subscription.Status.TRIAL and subscription.plan.trial_period_days > 0
            else Subscription.Status.ACTIVE
        )
    elif action == "pause":
        if current != Subscription.Status.ACTIVE:
            raise ValidationError({"status": "Only active subscriptions can be paused."})
        if not subscription.plan.allow_pause:
            raise ValidationError({"status": "This plan does not allow pausing."})
        subscription.status = Subscription.Status.PAUSED
    elif action == "resume":
        if current != Subscription.Status.PAUSED:
            raise ValidationError({"status": "Only paused subscriptions can be resumed."})
        subscription.status = Subscription.Status.ACTIVE
    elif action == "cancel":
        if current in {Subscription.Status.CANCELLED, Subscription.Status.EXPIRED, Subscription.Status.CLOSED}:
            raise ValidationError({"status": f"Cannot cancel a subscription in {current} state."})
        subscription.status = Subscription.Status.CANCELLED
        subscription.auto_renew = False
        subscription.cancellation_reason = cancellation_reason.strip()
        subscription.closed_at = now()
    else:
        raise ValidationError({"action": "Unsupported subscription action."})

    subscription.save()
    return subscription
