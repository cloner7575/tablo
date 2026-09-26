from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "phone",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "date_joined",
        )
        read_only_fields = ("id", "username", "role", "is_verified", "date_joined")

    def validate_email(self, value: str) -> str:
        email = (value or "").strip().lower()
        if not email:
            return email
        qs = User.objects.filter(email__iexact=email)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return email
