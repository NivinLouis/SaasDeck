from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("subscriptions", "0003_alter_subscription_status")]

    operations = [
        migrations.CreateModel(
            name="SubscriptionAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.CharField(max_length=64)),
                ("from_status", models.CharField(blank=True, max_length=20)),
                ("to_status", models.CharField(max_length=20)),
                ("reason", models.TextField(blank=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="subscription_audit_events", to=settings.AUTH_USER_MODEL)),
                ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="subscriptions.subscription")),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
        migrations.AddIndex(model_name="subscriptionauditevent", index=models.Index(fields=["subscription", "created_at"], name="sub_audit_timeline")),
    ]
