from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="Notification", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
        ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
        ("title", models.CharField(max_length=255)), ("body", models.TextField(blank=True)),
        ("category", models.CharField(default="system", max_length=32)), ("read_at", models.DateTimeField(blank=True, null=True)),
        ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ("-created_at",)}), migrations.AddIndex(model_name="notification", index=models.Index(fields=["recipient", "read_at"], name="notif_recipient_read"))]
