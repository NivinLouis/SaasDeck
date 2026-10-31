import re
from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    message = "Password must be at least 9 characters and include uppercase, lowercase, and a special character."

    def validate(self, password, user=None):
        if len(password) < 9 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(self.message, code="weak_password")

    def get_help_text(self):
        return self.message
