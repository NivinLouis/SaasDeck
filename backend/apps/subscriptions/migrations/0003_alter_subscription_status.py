from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0002_alter_quotationtemplateline_variant_and_more")]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"), ("QUOTATION", "Quotation Sent"), ("CONFIRMED", "Confirmed"),
                    ("TRIAL", "Trial"), ("ACTIVE", "Active"), ("PAUSED", "Paused"),
                    ("CANCELLED", "Cancelled"), ("EXPIRED", "Expired"), ("CLOSED", "Closed"),
                ],
                db_index=True,
                default="DRAFT",
                max_length=20,
            ),
        ),
    ]
