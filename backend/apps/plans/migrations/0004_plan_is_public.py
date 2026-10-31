from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("plans", "0003_plan_product_currency")]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="is_public",
            field=models.BooleanField(db_index=True, default=False, help_text="Show this plan in the customer software catalogue."),
        ),
    ]
