from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.services import request_otp, validate_phone
from apps.catalog.models import Service
from apps.locations.models import City
from apps.portfolio.models import PortfolioItem
from apps.quotes.models import Quote
from apps.requests.models import ProjectRequest
from apps.reviews.models import Review
from apps.vendors.models import Vendor


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "date_joined",
        )
        read_only_fields = fields


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value: str) -> str:
        return validate_phone(value)

    def create(self, validated_data):
        request_otp(phone=validated_data["phone"])
        return validated_data


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()

    def validate_phone(self, value: str) -> str:
        return validate_phone(value)


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "slug", "province", "is_active")


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ("id", "title", "slug", "description", "is_active", "sort_order")


class VendorSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Vendor
        fields = (
            "id",
            "business_name",
            "slug",
            "description",
            "phone",
            "city",
            "city_name",
            "address",
            "instagram",
            "website",
            "years_of_experience",
            "verification_status",
            "rating",
            "review_count",
            "completed_projects",
            "response_time_hours",
            "services",
            "is_featured",
            "logo",
        )


class ProjectRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRequest
        fields = (
            "id",
            "title",
            "description",
            "service",
            "city",
            "district",
            "business_type",
            "width_cm",
            "height_cm",
            "lighting_type",
            "budget_min",
            "budget_max",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "status", "created_at", "title")


class QuoteSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = Quote
        fields = (
            "id",
            "request",
            "vendor",
            "price",
            "estimated_delivery_days",
            "description",
            "warranty",
            "installation_cost",
            "material_details",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "vendor", "status", "created_at")


class QuoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = (
            "request",
            "price",
            "estimated_delivery_days",
            "description",
            "warranty",
            "installation_cost",
            "material_details",
        )


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioItem
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "service",
            "city",
            "image",
            "vendor",
            "created_at",
        )


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = (
            "id",
            "customer",
            "vendor",
            "request",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "customer", "created_at")
