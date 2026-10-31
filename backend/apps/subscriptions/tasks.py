"""Scheduled subscription lifecycle maintenance."""
from celery import shared_task

from .services import run_subscription_lifecycle


@shared_task(name="subscriptions.run_lifecycle")
def run_subscription_lifecycle_task():
    return run_subscription_lifecycle()
