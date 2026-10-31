from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("billing", "0006_billingrun_invoice_email_sent_at")]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="overdue_reminder_sent_at",
            field=models.DateTimeField(blank=True, help_text="When the overdue reminder was last delivered.", null=True),
        ),
    ]
