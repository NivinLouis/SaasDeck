# Generated manually to keep the catalog-plan relationship explicit.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_delete_productvariant_delete_taxrule_and_more"),
        ("plans", "0002_paymentterm_alter_plan_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="currency",
            field=models.CharField(default="INR", help_text="ISO 4217 currency code, e.g. INR or USD.", max_length=3),
        ),
        migrations.AddField(
            model_name="plan",
            name="product",
            field=models.ForeignKey(
                blank=True,
                help_text="Product or service sold through this recurring plan.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="plans",
                to="catalog.product",
            ),
        ),
    ]
