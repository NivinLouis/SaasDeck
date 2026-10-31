from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    dependencies = [("billing", "0003_alter_invoiceline_tax_rule")]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="customer_snapshot",
            field=models.JSONField(blank=True, default=dict, help_text="Immutable billing-contact snapshot used when rendering historical invoices."),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.CheckConstraint(condition=Q(("amount_paid__lte", F("total_amount"))), name="chk_invoice_amount_paid_lte_total"),
        ),
    ]
