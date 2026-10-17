from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import PhoneRequestOTPForm, PhoneVerifyOTPForm
from apps.accounts.models import UserRole
from apps.accounts.services import request_otp, verify_otp_and_login
from apps.analytics.services import track
from apps.catalog.models import Service
from apps.chat.selectors import unread_chat_count_for_customer
from apps.editorial.collections import saved_ideas
from apps.locations.models import City
from apps.orders.models import Order
from apps.orders.services import complete_order, create_review
from apps.portfolio.inspiration import board_items
from apps.quotes.models import Quote, QuoteStatus
from apps.quotes.services import accept_quote, mark_quote_viewed, toggle_shortlist
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
    SimpleDetailsForm,
    SimpleNeedForm,
    WorkspaceFilterForm,
)
from apps.requests.models import LightingType, ProjectRequest, RequestStatus
from apps.requests.panel import next_project_action
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
    if data.get("compact"):
        context.update(_compact_context(3))
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
    data = {"compact": True}
    service = Service.objects.filter(
        slug=request.GET.get("service", ""), is_active=True
    ).first()
    if service:
        data["service_id"] = service.pk
    elif request.GET.get("guidance") == "1":
        data["needs_guidance"] = True
    _save_wizard(request, data)
    return redirect("requests:wizard_need")


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
    if not _has_service_choice(data) or not data.get("city_id"):
        return redirect(
            "requests:wizard_need" if data.get("compact") else "requests:wizard_service"
        )

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
        context = _compact_context(3) if data.get("compact") else wizard_shell(9)
        context["back_url_name"] = (
            "requests:wizard_details"
            if data.get("compact")
            else "requests:wizard_budget"
        )
        context["recipient"] = _recipient(data)
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
    project_request.use_case = data.get("use_case", "")
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
    form = WorkspaceFilterForm(request.GET)
    valid = form.is_valid()
    summary = qs.aggregate(
        total=Count("pk", distinct=True),
        active=Count("pk", filter=Q(order__status="active"), distinct=True),
        completed=Count("pk", filter=Q(status=RequestStatus.COMPLETED), distinct=True),
        reviews=Count(
            "pk",
            filter=Q(status=RequestStatus.COMPLETED, review__isnull=True),
            distinct=True,
        ),
        new_quotes=Sum(
            "new_quote_count",
            filter=~Q(
                status__in=[
                    RequestStatus.ACCEPTED,
                    RequestStatus.COMPLETED,
                    RequestStatus.CANCELLED,
                ]
            ),
            default=0,
        ),
    )
    filtered = qs
    if valid:
        query = form.cleaned_data["q"]
        status = form.cleaned_data["status"]
        if query:
            filtered = filtered.filter(
                Q(title__icontains=query) | Q(business_type__icontains=query)
            )
        if status == "offers":
            filtered = filtered.filter(quote_count__gt=0).exclude(
                status__in=[
                    RequestStatus.COMPLETED,
                    RequestStatus.CANCELLED,
                    RequestStatus.ACCEPTED,
                ]
            )
        elif status == "active":
            filtered = filtered.filter(order__status="active")
        elif status:
            filtered = filtered.filter(status=status)
    else:
        filtered = qs.none()
    page_obj = Paginator(filtered, 12).get_page(request.GET.get("page"))
    projects = list(page_obj.object_list)
    filters = request.GET.copy()
    filters.pop("page", None)
    return render(
        request,
        "pages/dashboard/customer.html",
        {
            "form": form,
            "summary": summary,
            "page_obj": page_obj,
            "cards": [
                {"project": project, "action": next_project_action(project)}
                for project in projects
            ],
            "filter_query": filters.urlencode(),
            "has_filters": bool(filters),
            "customer_panel_active": "dashboard",
            "customer_unread_count": unread_chat_count_for_customer(user=request.user),
        },
        status=200 if valid else 400,
    )


@login_required
@require_http_methods(["POST"])
def quote_shortlist(request: HttpRequest, pk: int) -> HttpResponse:
    quote = get_object_or_404(
        Quote.objects.select_related("request"), pk=pk, request__customer=request.user
    )
    try:
        toggle_shortlist(quote=quote, user=request.user)
    except ValidationError as exc:
        messages.error(request, str(exc))
        return render(
            request,
            "pages/dashboard/shortlist_unavailable.html",
            {"quote": quote},
            status=400,
        )
    messages.success(
        request,
        "پیشنهاد به منتخب‌ها اضافه شد."
        if quote.status == QuoteStatus.SHORTLISTED
        else "پیشنهاد از منتخب‌ها برداشته شد.",
    )
    return redirect(
        reverse("requests:request_detail", kwargs={"pk": quote.request_id})
        + "#quotes-title"
    )


@login_required
@require_http_methods(["GET"])
def request_detail(request: HttpRequest, pk: int) -> HttpResponse:
    project_request = get_object_or_404(
        ProjectRequest.objects.select_related(
            "service",
            "city",
            "preferred_vendor",
            "review",
        ).prefetch_related("images", "quotes__vendor__city"),
        pk=pk,
        customer=request.user,
    )
    quotes = list(
        project_request.quotes.select_related("vendor", "vendor__city").order_by(
            "price", "-created_at"
        )
    )
    quotes.sort(
        key=lambda quote: (
            quote.status != QuoteStatus.SHORTLISTED,
            quote.total_price,
            -quote.pk,
        )
    )
    quotes_count = len(quotes)
    best_price = min((q.total_price for q in quotes), default=None)
    accepted = next((q for q in quotes if q.status == QuoteStatus.ACCEPTED), None)
    order = (
        Order.objects.select_related("vendor", "quote")
        .filter(request=project_request)
        .first()
    )

    status = project_request.status
    if status == RequestStatus.COMPLETED:
        journey_step = 4
    elif status == RequestStatus.ACCEPTED:
        journey_step = 4
    elif status in {RequestStatus.QUOTED, RequestStatus.NEGOTIATING}:
        journey_step = 3 if quotes_count else 2
    elif status in {
        RequestStatus.SUBMITTED,
        RequestStatus.REVIEWING,
        RequestStatus.RECEIVING_QUOTES,
    }:
        journey_step = 2 if quotes_count else 1
    else:
        journey_step = 1

    if status == RequestStatus.CANCELLED:
        next_title = "این درخواست لغو شده است"
        next_lead = "پیشنهادهای این درخواست دیگر قابل پذیرش نیستند."
        next_primary_url = reverse("requests:wizard_start")
        next_primary_label = "ثبت درخواست تازه"
    elif status == RequestStatus.DRAFT:
        next_title = "درخواست هنوز ارسال نشده است"
        next_lead = "این اطلاعات پیش‌نویس است و هنوز برای دریافت پیشنهاد ارسال نشده."
        next_primary_url = reverse("requests:wizard_start")
        next_primary_label = "شروع درخواست تازه"
    elif status == RequestStatus.COMPLETED and getattr(project_request, "review", None):
        next_title = "پروژه و بازخورد شما ثبت شده است"
        next_lead = "جزئیات این همکاری برای مراجعهٔ بعدی در میز کار شما می‌ماند."
        next_primary_url = reverse("requests:dashboard")
        next_primary_label = "بازگشت به پروژه‌ها"
    elif order is not None and order.status == "active":
        next_title = order.get_stage_display()
        next_lead = (
            "با تابلو‌ساز برنده هماهنگ کنید؛ وقتی کار تمام شد سفارش را تکمیل کنید."
        )
        next_primary_url = reverse("orders:progress", kwargs={"pk": order.pk})
        next_primary_label = "پیگیری سفارش"
    elif status == RequestStatus.COMPLETED and not getattr(
        project_request, "review", None
    ):
        next_title = "ثبت نظر"
        next_lead = "با یک نظر کوتاه به بقیه کمک کنید تابلو‌ساز مناسب را پیدا کنند."
        next_primary_url = reverse(
            "requests:review_create", kwargs={"pk": project_request.pk}
        )
        next_primary_label = "ثبت نظر و امتیاز"
    elif quotes_count == 0:
        next_title = "منتظر پیشنهادها بمانید"
        next_lead = (
            "درخواست شما برای دریافت پیشنهاد ثبت شده است. "
            "از همین صفحه آن را پیگیری کنید."
        )
        next_primary_url = ""
        next_primary_label = ""
    elif accepted:
        next_title = "پیشنهاد پذیرفته شد"
        next_lead = "جزئیات سفارش را در بنر بالای صفحه پیگیری کنید."
        next_primary_url = reverse("chat:thread", kwargs={"quote_id": accepted.pk})
        next_primary_label = "گفتگو با تابلو‌ساز"
    else:
        next_title = "مقایسه و انتخاب"
        next_lead = (
            f"{quotes_count} پیشنهاد دارید. قبل از پذیرش می‌توانید درباره قیمت "
            "و جزئیات گفتگو کنید."
        )
        next_primary_url = (
            reverse("requests:request_detail", kwargs={"pk": project_request.pk})
            + "#quotes-title"
        )
        next_primary_label = "مقایسهٔ پیشنهادها"

    return render(
        request,
        "pages/dashboard/request_detail.html",
        {
            "project_request": project_request,
            "photos": project_request.photo_urls(),
            "quotes": quotes,
            "quotes_count": quotes_count,
            "best_price": best_price,
            "journey_step": journey_step,
            "order": order,
            "next_title": next_title,
            "next_lead": next_lead,
            "next_primary_url": next_primary_url,
            "next_primary_label": next_primary_label,
            "customer_panel_active": "projects",
            "shortlisted_count": sum(
                1 for quote in quotes if quote.status == QuoteStatus.SHORTLISTED
            ),
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

    order = get_object_or_404(
        Order.objects.select_related("vendor", "request"), pk=pk, customer=request.user
    )
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

    vendor = get_object_or_404(
        Vendor, slug=slug, is_active=True, verification_status="approved"
    )
    _save_wizard(
        request,
        {
            "preferred_vendor_id": vendor.pk,
            "candidate_vendor_id": vendor.pk,
            "compact": True,
        },
    )
    track("quote_cta_clicked", {"vendor": slug})
    return redirect("requests:wizard_need")


@require_http_methods(["POST"])
def start_from_board(request: HttpRequest) -> HttpResponse:
    items = list(board_items(request))
    concepts = list(saved_ideas(request))
    if not items and not concepts:
        messages.info(request, _("ابتدا نمونه‌های مرجع پروژه را در بورد ذخیره کنید."))
        return redirect("editorial:saved")
    references = []
    for item in items:
        path = reverse("portfolio:detail", kwargs={"slug": item.slug})
        references.append(f"{item.title}: {request.build_absolute_uri(path)}")
    for idea in concepts:
        path = idea.get_absolute_url()
        references.append(
            f"مرجع ({idea.get_source_display()}، مفهومی): {idea.title}: "
            f"{request.build_absolute_uri(path)}"
        )
    description = "نمونه‌های مرجع برای سبک و اجرای پروژه:\n" + "\n".join(references)
    _save_wizard(request, {"description": description, "compact": True})
    messages.success(
        request, _("نمونه‌های مرجع اضافه شدند؛ مشخصات پروژه را تکمیل کنید.")
    )
    return redirect("requests:wizard_need")


COMPACT_STEPS = (
    {"number": 1, "label": "محل و نیاز"},
    {"number": 2, "label": "عکس و توضیح"},
    {"number": 3, "label": "بررسی و ثبت"},
)


def _compact_context(step: int) -> dict[str, object]:
    return {
        "step": step,
        "total": 3,
        "step_label": COMPACT_STEPS[step - 1]["label"],
        "wizard_steps": COMPACT_STEPS,
        "back_url_name": "requests:wizard_need"
        if step == 2
        else "requests:wizard_details"
        if step == 3
        else None,
    }


def _recipient(data: dict) -> str:
    from apps.vendors.models import Vendor

    if data.get("preferred_vendor_id"):
        vendor = Vendor.objects.filter(
            pk=data["preferred_vendor_id"],
            is_active=True,
            verification_status="approved",
        ).first()
        return (
            f"فقط {vendor.business_name}"
            if vendor
            else "تابلوساز انتخاب‌شده دیگر فعال نیست؛ دریافت‌کننده را دوباره انتخاب کنید."
        )
    return "تابلوسازهای مرتبط با نیاز شما در شهر انتخاب‌شده"


@require_http_methods(["GET", "POST"])
def wizard_need(request: HttpRequest) -> HttpResponse:
    from apps.vendors.models import Vendor

    data = _wizard_data(request)
    data["compact"] = True
    vendor = Vendor.objects.filter(
        pk=data.get("candidate_vendor_id") or data.get("preferred_vendor_id"),
        is_active=True,
        verification_status="approved",
    ).first()
    initial = {
        **data,
        "city": data.get("city_id"),
        "audience": "direct"
        if vendor and data.get("preferred_vendor_id")
        else "matched",
        "use_case": data.get("use_case", "shop"),
    }
    form = SimpleNeedForm(
        request.POST if request.method == "POST" else None,
        initial=initial,
        vendor_name=vendor.business_name if vendor else "",
    )
    if request.method == "POST" and form.is_valid():
        data.update(
            {
                "city_id": form.cleaned_data["city"].pk,
                "business_type": form.cleaned_data["business_type"],
                "use_case": form.cleaned_data["use_case"],
            }
        )
        if vendor:
            data["candidate_vendor_id"] = vendor.pk
        if form.cleaned_data["audience"] == "direct" and vendor:
            data["preferred_vendor_id"] = vendor.pk
        else:
            data.pop("preferred_vendor_id", None)
        _save_wizard(request, data)
        return redirect("requests:wizard_details")
    context = _compact_context(1)
    context.update(
        {
            "form": form,
            "simple_need": True,
            "step_title": "برای کجا تابلو می‌خواهید؟",
            "step_hint": "شهر و کسب‌وکارتان را بگویید؛ لازم نیست نوع تابلو را بشناسید.",
        }
    )
    return render(
        request,
        "pages/request/simple.html",
        context,
        status=400 if request.method == "POST" else 200,
    )


@require_http_methods(["GET", "POST"])
def wizard_details(request: HttpRequest) -> HttpResponse:
    data = _wizard_data(request)
    if not City.objects.filter(pk=data.get("city_id"), is_active=True).exists():
        return redirect("requests:wizard_need")
    data["compact"] = True
    initial = {
        **data,
        "choice": str(data["service_id"]) if data.get("service_id") else SERVICE_UNSURE,
        "night_light": data.get("night_light", "unsure"),
    }
    form = SimpleDetailsForm(
        request.POST if request.method == "POST" else None,
        request.FILES or None,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        cleaned = form.cleaned_data.copy()
        images = cleaned.pop("images", [])
        choice = cleaned.pop("choice") or SERVICE_UNSURE
        data.update(cleaned)
        data["needs_guidance"] = choice == SERVICE_UNSURE
        data["service_id"] = None if data["needs_guidance"] else int(choice)
        data["lighting_type"] = {"yes": LightingType.LED, "no": LightingType.NONE}.get(
            cleaned["night_light"], LightingType.UNSURE
        )
        data["size_choice"] = "" if cleaned.get("width_cm") else "unsure"
        if images:
            draft = (
                get_object_or_404(
                    ProjectRequest, pk=data["draft_id"], status=RequestStatus.DRAFT
                )
                if data.get("draft_id")
                else ProjectRequest.objects.create(status=RequestStatus.DRAFT)
            )
            replace_request_images(project_request=draft, files=images)
            data["draft_id"] = draft.pk
        _save_wizard(request, data)
        return redirect("requests:wizard_phone")
    context = _compact_context(2)
    context.update(
        {
            "form": form,
            "step_title": "چه چیزی مدنظر دارید؟",
            "step_hint": (
                "یک توضیح کوتاه و در صورت امکان عکس محل؛ "
                "جزئیات فنی را با تابلوساز نهایی کنید."
            ),
            "photo_count": _draft_photo_count(data.get("draft_id")),
            "recipient": _recipient(data),
        }
    )
    return render(
        request,
        "pages/request/simple.html",
        context,
        status=400 if request.method == "POST" else 200,
    )
