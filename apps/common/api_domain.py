from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.accounts.services import verify_otp_and_login
from apps.catalog.models import Service
from apps.common.serializers_domain import (
    CitySerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PortfolioSerializer,
    ProjectRequestSerializer,
    QuoteCreateSerializer,
    QuoteSerializer,
    ReviewSerializer,
    ServiceSerializer,
    UserSerializer,
    VendorSerializer,
)
from apps.locations.models import City
from apps.portfolio.models import PortfolioItem
from apps.quotes.models import Quote
from apps.quotes.services import accept_quote, create_quote
from apps.requests.models import ProjectRequest
from apps.requests.selectors import matched_requests_for_vendor
from apps.requests.services import submit_project_request
from apps.reviews.models import Review
from apps.vendors.models import Vendor, VerificationStatus


class OTPThrottle(AnonRateThrottle):
    scope = "otp"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([OTPThrottle])
def otp_request(request):
    serializer = OTPRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"detail": "کد ارسال شد."})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([OTPThrottle])
def otp_verify(request):
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user = verify_otp_and_login(
            request=request,
            phone=serializer.validated_data["phone"],
            code=serializer.validated_data["code"],
        )
    except ValidationError as exc:
        return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
    return Response(UserSerializer(user).data)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.filter(is_active=True).select_related("province")
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    search_fields = ["name", "slug"]
    ordering_fields = ["name"]


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    search_fields = ["title", "slug"]
    ordering_fields = ["sort_order", "title"]


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Vendor.objects.filter(
            is_active=True, verification_status=VerificationStatus.APPROVED
        )
        .select_related("city")
        .prefetch_related("services")
    )
    serializer_class = VendorSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    search_fields = ["business_name", "description"]
    ordering_fields = ["rating", "completed_projects"]


class ProjectRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ProjectRequest.objects.select_related("service", "city")
        if user.role == UserRole.VENDOR and hasattr(user, "vendor_profile"):
            return matched_requests_for_vendor(user.vendor_profile)
        return ProjectRequest.objects.filter(customer=user).select_related(
            "service", "city"
        )

    def perform_create(self, serializer):
        obj = serializer.save(customer=self.request.user)
        submit_project_request(project_request=obj)


class QuoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return QuoteCreateSerializer
        return QuoteSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Quote.objects.select_related("vendor", "request")
        if user.is_staff:
            return qs
        if user.role == UserRole.VENDOR and hasattr(user, "vendor_profile"):
            return qs.filter(vendor=user.vendor_profile)
        return qs.filter(request__customer=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not hasattr(request.user, "vendor_profile"):
            return Response(
                {"detail": "فقط تابلو‌ساز می‌تواند پیشنهاد بفرستد."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            quote = create_quote(
                vendor=request.user.vendor_profile,
                project_request=serializer.validated_data["request"],
                price=serializer.validated_data["price"],
                estimated_delivery_days=serializer.validated_data[
                    "estimated_delivery_days"
                ],
                description=serializer.validated_data.get("description", ""),
                warranty=serializer.validated_data.get("warranty", ""),
                installation_cost=serializer.validated_data.get("installation_cost", 0),
                material_details=serializer.validated_data.get("material_details", ""),
            )
        except (ValidationError, PermissionDenied) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(QuoteSerializer(quote).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        quote = self.get_object()
        try:
            order = accept_quote(quote=quote, user=request.user)
        except (ValidationError, PermissionDenied) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"order_id": order.pk, "status": "accepted"})


class PortfolioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PortfolioItem.objects.filter(is_published=True).select_related(
        "vendor", "service", "city"
    )
    serializer_class = PortfolioSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    search_fields = ["title", "description"]


class ReviewViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Review.objects.filter(is_published=True).select_related("vendor")
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
