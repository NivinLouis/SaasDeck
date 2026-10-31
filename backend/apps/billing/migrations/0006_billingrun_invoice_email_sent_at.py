from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("billing", "0005_gst_invoice_document_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="email_sent_at",
            field=models.DateTimeField(blank=True, help_text="When the latest invoice email was successfully sent.", null=True),
        ),
        migrations.CreateModel(
            name="BillingRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("run_date", models.DateField(db_index=True, help_text="The business date whose due subscriptions were processed.")),
                ("status", models.CharField(choices=[("RUNNING", "Running"), ("COMPLETED", "Completed"), ("PARTIAL", "Completed with errors"), ("FAILED", "Failed")], db_index=True, default="RUNNING", max_length=16)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("subscriptions_considered", models.PositiveIntegerField(default=0)),
                ("invoices_created", models.PositiveIntegerField(default=0)),
                ("invoices_existing", models.PositiveIntegerField(default=0)),
                ("failures", models.JSONField(blank=True, default=list)),
                ("triggered_by", models.ForeignKey(blank=True, help_text="Admin who started a manual run; blank for scheduled runs.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="triggered_billing_runs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "billing run",
                "verbose_name_plural": "billing runs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="billingrun",
            index=models.Index(fields=["run_date", "status"], name="idx_billing_run_date_status"),
        ),
    ]
