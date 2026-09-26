from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import PhoneRequestOTPForm, PhoneVerifyOTPForm
from apps.accounts.models import UserRole
from apps.accounts.services import request_otp, verify_otp_and_login
from apps.analytics.services import track
from apps.catalog.models import Service
from apps.locations.models import City
from apps.orders.services import complete_order, create_review
from apps.quotes.models import Quote
from apps.quotes.services import accept_quote, mark_quote_viewed
from apps.requests.forms import (
    SERVICE_UNSURE,
    RequestWizardBudgetForm,
    RequestWizardCityForm,
    RequestWizardDescriptionForm,
    RequestWizardDimensionsForm,
    RequestWizardImageForm,
    RequestWizardLightingForm,
    RequestWizardServiceForm,
    ReviewForm,
)
from apps.requests.models import LightingType, ProjectRequest, RequestStatus
from apps.requests.selectors import customer_requests
from apps.requests.services import replace_request_images, submit_project_request
from apps.requests.wizard_meta import wizard_shell

WIZARD_SESSION_KEY = "request_wizard"


def _wizard_data(request: HttpRequest) -> dict:
    return request.session.get(WIZARD_SESSION_KEY, {})


def _save_wizard(request: HttpRequest, data: dict) -> None:
    request.session[WIZARD_SESSION_KEY] = data
    request.session.modified = True


def _clear_wizard(request: HttpRequest) -> None:
    request.session.pop(WIZARD_SESSION_KEY, None)


def _has_service_choice(data: dict) -> bool:
    return bool(data.get("service_id") or data.get("needs_guidance"))


def _render_wizard(
    request: HttpRequest,
    *,
    form: object,
    step: int,
    enctype: bool = False,
    step_title: str | None = None,
    step_hint: str | None = None,
    extra: dict | None = None,
) -> HttpResponse:
    context = wizard_shell(step, step_title=step_title, step_hint=step_hint)
    context.update({"form": form, "enctype": enctype})
    data = _wizard_data(request)
    if data.get("needs_guidance"):
        context["beginner_banner"] = (
            "اشکالی ندارد که جزئیات را ندانید — "
            "تابلو‌سازها با عکس و توضیح ساده راهنمایی‌تان می‌کنند."
        )
    if extra:
        context.update(extra)
    return render(request, "pages/request/wizard.html", context)


def _wizard_summary(data: dict) -> dict[str, str]:
    service = Service.objects.filter(pk=data.get("service_id")).first()
    city = City.objects.filter(pk=data.get("city_id")).first()
    lighting = data.get("lighting_type") or ""
    lighting_label = dict(LightingType.choices).get(lighting, "—")
    size_choice = data.get("size_choice") or ""
    size_labels = {
        "small": "کوچک (حدود ۱ متر)",
        "medium": "متوسط (حدود ۲٫۵ متر)",
        "large": "بزرگ (حدود ۴ متر یا بیشتر)",
        "unsure": "هنوز مشخص نیست",
    }
    dims = size_labels.get(size_choice)
    if not dims:
        width = data.get("width_cm")
        height = data.get("height_cm")
        dims = "—"
        if width and height:
            dims = f"{width} × {height} سانتی‌متر"
    budget_min = data.get("budget_min")
    budget_max = data.get("budget_max")
    budget = "—"
    if budget_min or budget_max:
        lo = f"{budget_min:,}" if budget_min else "—"
        hi = f"{budget_max:,}" if budget_max else "—"
        budget = f"{lo} تا {hi} تومان"
    if data.get("needs_guidance"):
        service_label = "هنوز مطمئن نیستم — راهنمایی می‌خواهم"
    else:
        service_label = service.title if service else "—"
    return {
        "service": service_label,
        "city": city.name if city else "—",
        "dimensions": dims,
        "lighting": str(lighting_label),
        "description": data.get("description") or "—",
        "text_content": data.get("text_content") or "—",
        "business_type": data.get("business_type") or "—",
        "district": data.get("district") or "—",
        "budget": budget,
        "photo_count": _draft_photo_count(data.get("draft_id")),
        "needs_guidance": data.get("needs_guidance", False),
    }


def _draft_photo_count(draft_id: int | None) -> int:
    if not draft_id:
        return 0
    draft = (
        ProjectRequest.objects.filter(pk=draft_id).prefetch_related("images").first()
    )
    if draft is None:
        return 0
    return draft.photo_count


@require_http_methods(["GET", "POST"])
def wizard_start(request: HttpRequest) -> HttpResponse:
    track("quote_cta_clicked", {})
    track("request_started", {})
    preferred = _wizard_data(request).get("preferred_vendor_id")
    _save_wizard(request, {"preferred_vendor_id": preferred} if preferred else {})
    return redirect("requests:wizard_service")


@require_http_methods(["GET", "POST"])
def wizard_service(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    initial = {}
    if data.get("needs_guidance"):
        initial["choice"] = SERVICE_UNSURE
    elif data.get("service_id"):
        initial["choice"] = str(data["service_id"])
    form = RequestWizardServiceForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        choice = form.cleaned_data["choice"]
        if choice == SERVICE_UNSURE:
            data.pop("service_id", None)
            data["needs_guidance"] = True
        else:
            data["service_id"] = int(choice)
            data["needs_guidance"] = False
        _save_wizard(request, data)
        return redirect("requests:wizard_city")
    return _render_wizard(
        request,
        form=form,
        step=1,
        extra={
            "choice_cards": form.service_cards,
            "choice_field_name": "choice",
            "choice_selected": initial.get("choice", ""),
            "choice_legend": form.fields["choice"].label,
        },
    )


@require_http_methods(["GET", "POST"])
def wizard_city(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    if not _has_service_choice(data):
        return redirect("requests:wizard_start")
    form = RequestWizardCityForm(request.POST or None, initial=data)
    if request.method == "POST" and form.is_valid():
        data["city_id"] = form.cleaned_data["city"].pk
        _save_wizard(request, data)
        return redirect("requests:wizard_dimensions")
    return _render_wizard(request, form=form, step=2)


@require_http_methods(["GET", "POST"])
def wizard_dimensions(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    if "city_id" not in data:
        return redirect("requests:wizard_start")
    form = RequestWizardDimensionsForm(request.POST or None, initial=data)
    if request.method == "POST" and form.is_valid():
        size_choice = form.cleaned_data["size_choice"]
        width, height = form.resolved_dimensions()
        data["size_choice"] = size_choice
        data["width_cm"] = width
        data["height_cm"] = height
        _save_wizard(request, data)
        return redirect("requests:wizard_lighting")
    return _render_wizard(
        request,
        form=form,
        step=3,
        extra={
            "choice_cards": form.size_cards,
            "choice_field_name": "size_choice",
            "choice_selected": data.get("size_choice") or "",
            "choice_legend": form.fields["size_choice"].label,
        },
    )


@require_http_methods(["GET", "POST"])
def wizard_lighting(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    form = RequestWizardLightingForm(request.POST or None, initial=data)
    if request.method == "POST" and form.is_valid():
        data["lighting_type"] = form.cleaned_data["lighting_type"]
        _save_wizard(request, data)
        return redirect("requests:wizard_description")
    selected = data.get("lighting_type") or LightingType.UNSURE
    return _render_wizard(
        request,
        form=form,
        step=4,
        extra={
            "choice_cards": form.lighting_cards,
            "choice_field_name": "lighting_type",
            "choice_selected": selected,
            "choice_legend": form.fields["lighting_type"].label,
        },
    )


@require_http_methods(["GET", "POST"])
def wizard_description(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    form = RequestWizardDescriptionForm(
        request.POST or None,
        initial=data,
        needs_guidance=bool(data.get("needs_guidance")),
    )
    if request.method == "POST" and form.is_valid():
        data.update(form.cleaned_data)
        _save_wizard(request, data)
        return redirect("requests:wizard_image")
    return _render_wizard(request, form=form, step=5)


@require_http_methods(["GET", "POST"])
def wizard_image(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    form = RequestWizardImageForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        images = form.cleaned_data.get("images") or []
        if images:
            draft_id = data.get("draft_id")
            if draft_id:
                draft = get_object_or_404(ProjectRequest, pk=draft_id)
            else:
                draft = ProjectRequest.objects.create(status=RequestStatus.DRAFT)
            replace_request_images(project_request=draft, files=images)
            data["draft_id"] = draft.pk
        _save_wizard(request, data)
        return redirect("requests:wizard_budget")
    return _render_wizard(
        request,
        form=form,
        step=6,
        enctype=True,
        extra={"multi_image": True},
    )


@require_http_methods(["GET", "POST"])
def wizard_budget(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    form = RequestWizardBudgetForm(request.POST or None, initial=data)
    if request.method == "POST" and form.is_valid():
        data.update({k: v for k, v in form.cleaned_data.items() if v is not None})
        _save_wizard(request, data)
        return redirect("requests:wizard_phone")
    return _render_wizard(request, form=form, step=7)


@require_http_methods(["GET", "POST"])
def wizard_phone(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    if not data.get("service_id"):
        return redirect("requests:wizard_start")

    if request.user.is_authenticated:
        return redirect("requests:wizard_submit")

    form = PhoneRequestOTPForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            request_otp(phone=form.cleaned_data["phone"], purpose="request")
        except ValidationError as exc:
            form.add_error("phone", exc.message)
        else:
            data["phone"] = form.cleaned_data["phone"]
            _save_wizard(request, data)
            return redirect("requests:wizard_otp")
    return _render_wizard(request, form=form, step=8)


@require_http_methods(["GET", "POST"])
def wizard_otp(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    phone = data.get("phone")
    if not phone:
        return redirect("requests:wizard_phone")
    form = PhoneVerifyOTPForm(request.POST or None, initial={"phone": phone})
    if request.method == "POST" and form.is_valid():
        try:
            verify_otp_and_login(
                request=request,
                phone=form.cleaned_data["phone"],
                code=form.cleaned_data["code"],
                purpose="request",
                role=UserRole.CUSTOMER,
            )
        except ValidationError as exc:
            form.add_error("code", exc.message)
        else:
            return redirect("requests:wizard_submit")
    return _render_wizard(
        request,
        form=form,
        step=8,
        step_title="کد تأیید را وارد کنید",
        step_hint=f"کد پیامک‌شده به {phone} را وارد کنید.",
        extra={"back_url_name": "requests:wizard_phone"},
    )


@require_http_methods(["GET", "POST"])
def wizard_submit(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("requests:wizard_phone")

    data = _wizard_data(request)
    if not data.get("city_id") or not _has_service_choice(data):
        return redirect("requests:wizard_start")

    if request.method == "GET":
        context = wizard_shell(9)
        context["summary"] = _wizard_summary(data)
        context["data"] = data
        return render(request, "pages/request/wizard_confirm.html", context)

    preferred_vendor_id = data.get("preferred_vendor_id")
    draft_id = data.get("draft_id")
    if draft_id:
        project_request = get_object_or_404(ProjectRequest, pk=draft_id)
    else:
        project_request = ProjectRequest(status=RequestStatus.DRAFT)

    project_request.customer = request.user
    project_request.needs_guidance = bool(data.get("needs_guidance"))
    project_request.service_id = data.get("service_id")
    project_request.city_id = data["city_id"]
    project_request.size_choice = data.get("size_choice") or ""
    project_request.width_cm = data.get("width_cm")
    project_request.height_cm = data.get("height_cm")
    project_request.lighting_type = data.get("lighting_type", "")
    project_request.description = data.get("description", "")
    project_request.text_content = data.get("text_content", "")
    project_request.business_type = data.get("business_type", "")
    project_request.district = data.get("district", "")
    project_request.budget_min = data.get("budget_min")
    project_request.budget_max = data.get("budget_max")
    if preferred_vendor_id:
        project_request.preferred_vendor_id = preferred_vendor_id
    project_request.save()

    submit_project_request(project_request=project_request)
    _clear_wizard(request)
    messages.success(request, "درخواست شما ثبت شد.")
    return redirect("requests:success", pk=project_request.pk)


@require_http_methods(["GET"])
def request_success(request: HttpRequest, pk: int) -> HttpResponse:
    project_request = get_object_or_404(
        ProjectRequest.objects.select_related("service", "city"),
        pk=pk,
    )
    return render(
        request,
        "pages/request/success.html",
        {"project_request": project_request},
    )


@login_required
@require_http_methods(["GET"])
def customer_dashboard(request: HttpRequest) -> HttpResponse:
    qs = customer_requests(request.user)
    return render(
        request,
        "pages/dashboard/customer.html",
        {
            "requests": qs,
            "active": qs.exclude(
                status__in=[RequestStatus.COMPLETED, RequestStatus.CANCELLED]
            ),
            "completed": qs.filter(status=RequestStatus.COMPLETED),
        },
    )


@login_required
@require_http_methods(["GET"])
def request_detail(request: HttpRequest, pk: int) -> HttpResponse:
    project_request = get_object_or_404(
        ProjectRequest.objects.select_related(
            "service", "city", "order", "preferred_vendor"
        ).prefetch_related("images", "quotes__vendor__city"),
        pk=pk,
        customer=request.user,
    )
    quotes = list(project_request.quotes.select_related("vendor", "vendor__city"))
    return render(
        request,
        "pages/dashboard/request_detail.html",
        {
            "project_request": project_request,
            "photos": project_request.photo_urls(),
            "quotes": quotes,
            "quotes_count": len(quotes),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def quote_detail(request: HttpRequest, pk: int) -> HttpResponse:
    quote = get_object_or_404(
        Quote.objects.select_related("vendor", "vendor__city", "request"),
        pk=pk,
        request__customer=request.user,
    )
    mark_quote_viewed(quote=quote, user=request.user)
    if request.method == "POST":
        try:
            accept_quote(quote=quote, user=request.user)
        except (ValidationError, PermissionError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "پیشنهاد پذیرفته شد.")
            return redirect("requests:request_detail", pk=quote.request_id)
    return render(request, "pages/dashboard/quote_detail.html", {"quote": quote})


@login_required
@require_http_methods(["POST"])
def order_complete(request: HttpRequest, pk: int) -> HttpResponse:
    from apps.orders.models import Order

    order = get_object_or_404(Order, pk=pk)
    try:
        complete_order(order=order, user=request.user)
    except (ValidationError, PermissionError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "پروژه تکمیل شد. می‌توانید نظر ثبت کنید.")
    return redirect("requests:request_detail", pk=order.request_id)


@login_required
@require_http_methods(["GET", "POST"])
def review_create(request: HttpRequest, pk: int) -> HttpResponse:
    project_request = get_object_or_404(ProjectRequest, pk=pk, customer=request.user)
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_review(
                user=request.user,
                project_request=project_request,
                rating=form.cleaned_data["rating"],
                comment=form.cleaned_data.get("comment", ""),
            )
        except (ValidationError, PermissionError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "نظر شما ثبت شد.")
            return redirect("requests:request_detail", pk=pk)
    return render(
        request,
        "pages/dashboard/review_form.html",
        {"form": form, "project_request": project_request},
    )


@require_http_methods(["GET"])
def start_for_vendor(request: HttpRequest, slug: str) -> HttpResponse:
    from apps.vendors.models import Vendor

    vendor = get_object_or_404(Vendor, slug=slug, is_active=True)
    _save_wizard(request, {"preferred_vendor_id": vendor.pk})
    track("quote_cta_clicked", {"vendor": slug})
    return redirect("requests:wizard_service")
