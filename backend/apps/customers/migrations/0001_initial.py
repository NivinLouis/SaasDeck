import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)), ("company", models.CharField(blank=True, max_length=255)),
                ("email", models.EmailField(max_length=254)), ("phone", models.CharField(blank=True, max_length=32)),
                ("billing_address", models.TextField(blank=True)), ("city", models.CharField(blank=True, max_length=128)),
                ("state", models.CharField(blank=True, max_length=128)), ("country", models.CharField(blank=True, max_length=128)),
                ("postal_code", models.CharField(blank=True, max_length=32)), ("tax_id", models.CharField(blank=True, max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_customers", to=settings.AUTH_USER_MODEL)),
                ("user", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="customer_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.AddIndex(model_name="customer", index=models.Index(fields=["email"], name="customers_c_email_2bd4fb_idx")),
    ]
