from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import migrations, models


GSTIN_VALIDATOR = RegexValidator(message="Enter a valid 15-character GSTIN.", regex=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$")
STATE_CODE_VALIDATOR = RegexValidator(message="Enter the two-digit GST state code.", regex=r"^[0-9]{2}$")


class Migration(migrations.Migration):
    dependencies = [("billing", "0004_invoice_customer_snapshot_and_paid_limit")]

    operations = [
        migrations.AddField(model_name="invoice", name="supplier_legal_name", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="invoice", name="supplier_address", field=models.TextField(blank=True)),
        migrations.AddField(model_name="invoice", name="supplier_gstin", field=models.CharField(blank=True, max_length=15, validators=[GSTIN_VALIDATOR])),
        migrations.AddField(model_name="invoice", name="supplier_state_name", field=models.CharField(blank=True, max_length=128)),
        migrations.AddField(model_name="invoice", name="supplier_state_code", field=models.CharField(blank=True, max_length=2, validators=[STATE_CODE_VALIDATOR])),
        migrations.AddField(model_name="invoice", name="supplier_authorised_signatory", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="invoice", name="recipient_legal_name", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="invoice", name="recipient_address", field=models.TextField(blank=True)),
        migrations.AddField(model_name="invoice", name="recipient_gstin", field=models.CharField(blank=True, max_length=15, validators=[GSTIN_VALIDATOR])),
        migrations.AddField(model_name="invoice", name="recipient_state_name", field=models.CharField(blank=True, max_length=128)),
        migrations.AddField(model_name="invoice", name="recipient_state_code", field=models.CharField(blank=True, max_length=2, validators=[STATE_CODE_VALIDATOR])),
        migrations.AddField(model_name="invoice", name="place_of_supply_state_name", field=models.CharField(blank=True, max_length=128)),
        migrations.AddField(model_name="invoice", name="place_of_supply_state_code", field=models.CharField(blank=True, max_length=2, validators=[STATE_CODE_VALIDATOR])),
        migrations.AddField(model_name="invoice", name="reverse_charge", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="invoice", name="irn", field=models.CharField(blank=True, help_text="Invoice Reference Number from the IRP, if applicable.", max_length=64)),
        migrations.AddField(model_name="invoice", name="acknowledgement_number", field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name="invoice", name="acknowledgement_date", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="invoiceline", name="hsn_sac", field=models.CharField(blank=True, help_text="HSN for goods or SAC for services, captured as an invoice snapshot.", max_length=16)),
        migrations.AddField(model_name="invoiceline", name="unit", field=models.CharField(default="NOS", help_text="Unit or UQC, for example NOS, MONTH or YEAR.", max_length=16)),
        migrations.AddField(model_name="invoiceline", name="cess_rate_percent", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5, validators=[MinValueValidator(Decimal("0.00"))])),
        migrations.AddField(model_name="invoiceline", name="cess_amount", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[MinValueValidator(Decimal("0.00"))])),
    ]
