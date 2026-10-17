from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.orders.forms import DesignDecisionForm, DesignProposalForm, OrderStageForm
from apps.orders.models import Order
from apps.orders.services import (
    advance_order,
    approve_design,
    propose_design,
    request_design_changes,
)


@login_required
@require_http_methods(["GET", "POST"])
def progress(request: HttpRequest, pk: int) -> HttpResponse:
    from django.db.models import Q

    order = get_object_or_404(
        Order.objects.select_related("request", "quote", "vendor", "customer"),
        Q(customer=request.user) | Q(vendor__user=request.user),
        pk=pk,
    )
    is_customer = order.customer_id == request.user.pk
    initial = {
        "price": order.proposed_price
        if order.proposed_price is not None
        else order.quote.price,
        "installation_cost": order.proposed_installation_cost
        if order.proposed_installation_cost is not None
        else order.quote.installation_cost,
        "materials": order.materials or order.quote.material_details,
        "notes": order.design_notes,
    }
    proposal_form = DesignProposalForm(initial=initial)
    decision_form = DesignDecisionForm(initial={"version": order.proposal_version})
    stage_form = OrderStageForm()
    if request.method == "POST":
        if is_customer:
            form = decision_form = DesignDecisionForm(request.POST)
        elif request.POST.get("operation") == "stage":
            form = stage_form = OrderStageForm(request.POST)
        else:
            form = proposal_form = DesignProposalForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                if is_customer and form.cleaned_data["action"] == "approve":
                    approve_design(
                        order=order,
                        user=request.user,
                        version=form.cleaned_data["version"],
                    )
                elif is_customer:
                    request_design_changes(
                        order=order,
                        user=request.user,
                        notes=form.cleaned_data["notes"],
                        version=form.cleaned_data["version"],
                    )
                elif request.POST.get("operation") == "stage":
                    advance_order(
                        order=order, user=request.user, stage=form.cleaned_data["stage"]
                    )
                else:
                    propose_design(order=order, user=request.user, **form.cleaned_data)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, "مرحلهٔ سفارش به‌روز شد.")
                return redirect("orders:progress", pk=order.pk)
    context = {
        "order": order,
        "project_request": order.request,
        "is_customer": is_customer,
        "proposal_form": proposal_form,
        "decision_form": decision_form,
        "stage_form": stage_form,
        "customer_panel_active": "projects",
    }
    if not is_customer:
        from apps.vendors.panel import panel_context

        context = panel_context(order.vendor, "projects", **context)
    return render(
        request,
        "pages/orders/progress.html",
        context,
        status=400 if request.method == "POST" else 200,
    )
