from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate_user(self, user):
        if user and user.role != "customer":
            raise serializers.ValidationError("Only a customer account can be linked to a customer profile.")
        return user
