"""Validated, immutable operation previews and transactional, idempotent execution."""

import hashlib
import json
import uuid
from datetime import timedelta
from typing import Annotated, Literal

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from apps.integrations.auth import eligible
from apps.integrations.models import AuditEvent, Connection, DesignAsset, Operation


class StrictAction(BaseModel):
    model_config = ConfigDict(extra='forbid')


class QuoteAction(StrictAction):
    kind: Literal['quote']
    request_id: int
    price: int = Field(ge=0)
    installation_cost: int = Field(default=0, ge=0)
    price_kind: Literal['estimate', 'final'] = 'estimate'
    estimated_delivery_days: int = Field(ge=1, le=3650)
    description: str = Field(default='', max_length=5000)
    warranty: str = Field(default='', max_length=500)
    material_details: str = Field(default='', max_length=5000)


class MessageAction(StrictAction):
    kind: Literal['message']
    conversation_id: int
    body: str = Field(min_length=1, max_length=4000)


class DesignAction(StrictAction):
    kind: Literal['design']
    order_id: int
    asset_id: uuid.UUID
    price: int = Field(ge=0)
    installation_cost: int = Field(ge=0)
    materials: str = Field(min_length=1, max_length=5000)
    notes: str = Field(min_length=1, max_length=5000)


class StageAction(StrictAction):
    kind: Literal['stage']
    order_id: int
    stage: Literal['installation', 'delivered']


class ProfileAction(StrictAction):
    kind: Literal['profile']
    business_name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    phone: str | None = None
    city: int | None = None
    address: str | None = None
    instagram: str | None = None
    website: str | None = None
    years_of_experience: int | None = Field(default=None, ge=0)
    services: list[int] | None = None
    logo_asset_id: uuid.UUID | None = None
    cover_asset_id: uuid.UUID | None = None


class PortfolioAction(StrictAction):
    kind: Literal['portfolio']
    portfolio_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=10000)
    service: int
    city: int
    asset_id: uuid.UUID | None = None


class PublishAction(StrictAction):
    kind: Literal['publish']
    portfolio_id: int
    published: bool = True


Action = Annotated[
    QuoteAction
    | MessageAction
    | DesignAction
    | StageAction
    | ProfileAction
    | PortfolioAction
    | PublishAction,
    Field(discriminator='kind'),
]
action_adapter = TypeAdapter(Action)
AI_LABEL = 'طرح مفهومی تولیدشده با هوش مصنوعی'


def asset_file(asset: DesignAsset) -> SimpleUploadedFile:
    with asset.image.open('rb') as source:
        return SimpleUploadedFile(
            f'{asset.pk}.png', source.read(), content_type='image/png'
        )


def apply_action(
    connection: Connection, action: Action, execute: bool = False
) -> dict[str, object]:
    from apps.chat.models import Conversation
    from apps.chat.services import send_message
    from apps.integrations.tools.read import visible_requests
    from apps.orders.models import Order
    from apps.orders.services import advance_order, propose_design
    from apps.portfolio.forms import PortfolioForm
    from apps.portfolio.models import PortfolioItem
    from apps.portfolio.services import create_item, update_item
    from apps.quotes.forms import QuoteForm
    from apps.quotes.services import create_quote
    from apps.vendors.forms import VendorProfileForm

    eligible(connection)
    if "vendor:write" not in connection.scopes.split():
        raise PermissionDenied("مجوز تغییر اطلاعات داده نشده است.")
    from apps.vendors.models import Vendor

    vendor = Vendor.objects.select_related("user").get(pk=connection.vendor_id)
    if isinstance(action, QuoteAction):
        item = get_object_or_404(visible_requests(vendor.pk), pk=action.request_id)
        values = action.model_dump(exclude={'kind', 'request_id'})
        form = QuoteForm(values)
        if not form.is_valid():
            raise ValidationError(form.errors.as_json())
        if execute:
            # Serialize submissions from this account, including separate drafts.
            from apps.vendors.models import Vendor

            Vendor.objects.select_for_update().get(pk=vendor.pk)
            result = create_quote(
                vendor=vendor, project_request=item, **form.cleaned_data
            )
            return {'quote_id': result.pk}
    elif isinstance(action, MessageAction):
        conversation = get_object_or_404(
            Conversation.objects.select_related('quote__request', 'quote__vendor'),
            pk=action.conversation_id,
            quote__vendor=vendor,
        )
        if execute:
            result = send_message(
                quote=conversation.quote, user=vendor.user, body=action.body
            )
            return {'message_id': result.pk}
    elif isinstance(action, DesignAction):
        order = get_object_or_404(Order, pk=action.order_id, vendor=vendor)
        asset = get_object_or_404(DesignAsset, pk=action.asset_id, vendor=vendor)
        if asset.order_id and asset.order_id != order.pk:
            raise ValidationError('این تصویر متعلق به پروژه دیگری است.')
        if execute:
            result = propose_design(
                order=order,
                user=vendor.user,
                image=asset_file(asset),
                price=action.price,
                installation_cost=action.installation_cost,
                materials=action.materials,
                notes=action.notes + '\n' + AI_LABEL,
            )
            return {'order_id': result.pk, 'version': result.proposal_version}
    elif isinstance(action, StageAction):
        order = get_object_or_404(Order, pk=action.order_id, vendor=vendor)
        if execute:
            result = advance_order(order=order, user=vendor.user, stage=action.stage)
            return {'order_id': result.pk, 'stage': result.stage}
    elif isinstance(action, ProfileAction):
        fields = list(VendorProfileForm._meta.fields)
        values = {
            key: getattr(vendor, key + '_id' if key == 'city' else key)
            for key in fields
            if key not in {'services', 'logo', 'cover_image'}
        }
        values['services'] = list(vendor.services.values_list('pk', flat=True))
        patch = action.model_dump(
            exclude_unset=True, exclude={'kind', 'logo_asset_id', 'cover_asset_id'}
        )
        if any(value is None for value in patch.values()):
            raise ValidationError(
                'برای پاک کردن متن از رشته خالی استفاده کنید؛ مقدار null مجاز نیست.'
            )
        values.update(patch)
        files = {}
        for key, asset_id in [
            ('logo', action.logo_asset_id),
            ('cover_image', action.cover_asset_id),
        ]:
            if asset_id:
                files[key] = asset_file(
                    get_object_or_404(DesignAsset, pk=asset_id, vendor=vendor)
                )
        form = VendorProfileForm(values, files=files, instance=vendor)
        if not form.is_valid():
            raise ValidationError(form.errors.as_json())
        if execute:
            form.save()
            return {'vendor_id': vendor.pk}
    elif isinstance(action, PortfolioAction):
        item = (
            get_object_or_404(PortfolioItem, pk=action.portfolio_id, vendor=vendor)
            if action.portfolio_id
            else PortfolioItem(vendor=vendor)
        )
        if item.is_published and action.portfolio_id:
            raise ValidationError(
                'ابتدا انتشار نمونه‌کار را متوقف کنید تا نسخه جدید آماده شود.'
            )
        asset = (
            get_object_or_404(DesignAsset, pk=action.asset_id, vendor=vendor)
            if action.asset_id
            else None
        )
        description = action.description
        is_concept = bool(asset) or (
            bool(item.pk) and DesignAsset.objects.filter(portfolio=item).exists()
        )
        if is_concept:
            description = AI_LABEL + '\n' + description
        form = PortfolioForm(
            {
                'title': action.title,
                'description': description,
                'service': action.service,
                'city': action.city,
                'is_published': False,
            },
            files={'image': asset_file(asset)} if asset else None,
            instance=item,
        )
        if not form.is_valid():
            raise ValidationError(form.errors.as_json())
        if execute:
            item = form.save(commit=False)
            if is_concept:
                item.is_ai_concept = True
            (update_item if item.pk else create_item)(item=item)
            if asset:
                asset.portfolio = item
                asset.save(update_fields=['portfolio', 'updated_at'])
            return {'portfolio_id': item.pk}
    elif isinstance(action, PublishAction):
        item = get_object_or_404(PortfolioItem, pk=action.portfolio_id, vendor=vendor)
        if execute:
            item.is_published = action.published
            item.save(update_fields=['is_published', 'updated_at'])
            return {'portfolio_id': item.pk, 'published': item.is_published}
    return {'preview': action.model_dump(mode='json', exclude_unset=True)}


@transaction.atomic
def prepare(connection: Connection, action: Action) -> Operation:
    apply_action(connection, action)
    return Operation.objects.create(
        connection=connection,
        kind=action.kind,
        payload=action.model_dump(mode='json', exclude_unset=True),
        target_version=target_version(connection, action),
        expires_at=timezone.now() + timedelta(minutes=30),
    )


@transaction.atomic
def execute_operation(
    connection: Connection, operation_id: uuid.UUID
) -> dict[str, object]:
    locked = Connection.objects.select_for_update().get(pk=connection.pk)
    eligible(locked)
    operation = get_object_or_404(
        Operation.objects.select_for_update(), pk=operation_id, connection=locked
    )
    if operation.executed_at:
        return operation.result
    if operation.expires_at <= timezone.now():
        raise ValidationError('پیش‌نویس منقضی شده است؛ دوباره آماده کنید.')
    action = action_adapter.validate_python(operation.payload)
    if operation.target_version != target_version(locked, action, lock=True):
        raise ValidationError(
            'اطلاعات پس از پیش‌نمایش تغییر کرده است؛ پیش‌نویس تازه بسازید.'
        )
    result = apply_action(
        locked, action_adapter.validate_python(operation.payload), execute=True
    )
    operation.result = result
    operation.executed_at = timezone.now()
    operation.save(update_fields=['result', 'executed_at'])
    AuditEvent.objects.create(
        connection=locked, action=operation.kind, object_id=str(operation.pk)
    )
    return result


def target_version(connection: Connection, action: Action, lock: bool = False) -> str:
    from apps.orders.models import Order
    from apps.portfolio.models import PortfolioItem

    values: list[str] = []

    def owned(
        model: type[Order] | type[PortfolioItem] | type[DesignAsset], pk: object
    ) -> object:
        queryset = model.objects.select_for_update() if lock else model.objects.all()
        return get_object_or_404(queryset, pk=pk, vendor=connection.vendor)

    if isinstance(action, (DesignAction, StageAction)):
        row = owned(Order, action.order_id)
        values.append(row.updated_at.isoformat())
    if isinstance(action, (PortfolioAction, PublishAction)) and action.portfolio_id:
        row = owned(PortfolioItem, action.portfolio_id)
        values.append(row.updated_at.isoformat())
    if isinstance(action, ProfileAction):
        from apps.vendors.models import Vendor

        queryset = Vendor.objects.select_for_update() if lock else Vendor.objects.all()
        row = queryset.get(pk=connection.vendor_id)
        values.append(row.updated_at.isoformat())
    asset_id = getattr(action, 'asset_id', None)
    if asset_id:
        row = owned(DesignAsset, asset_id)
        values.append(row.updated_at.isoformat())
    return hashlib.sha256(json.dumps(values).encode()).hexdigest()
