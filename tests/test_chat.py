from __future__ import annotations

import pytest
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.catalog.models import Service
from apps.chat.models import Conversation, ConversationStatus, Message
from apps.chat.services import (
    ChatError,
    get_or_open_conversation,
    send_message,
)
from apps.locations.models import City, Province
from apps.quotes.models import QuoteStatus
from apps.quotes.services import accept_quote, create_quote
from apps.requests.models import LightingType, ProjectRequest, RequestStatus
from apps.requests.services import submit_project_request
from apps.vendors.models import Vendor, VerificationStatus
from core.asgi import application

User = get_user_model()


@pytest.fixture
def province(db):
    return Province.objects.create(name="تهران", slug="tehran-chat")


@pytest.fixture
def city(province):
    return City.objects.create(name="تهران", slug="tehran-chat", province=province)


@pytest.fixture
def service(db):
    return Service.objects.create(title="نئون", slug="neon-chat", sort_order=2)


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username="09121110001",
        phone="09121110001",
        role=UserRole.CUSTOMER,
        is_verified=True,
        password="x",
    )


@pytest.fixture
def vendor_user(db):
    return User.objects.create_user(
        username="09122220001",
        phone="09122220001",
        role=UserRole.VENDOR,
        is_verified=True,
        password="x",
    )


@pytest.fixture
def outsider(db):
    return User.objects.create_user(
        username="09123330001",
        phone="09123330001",
        role=UserRole.CUSTOMER,
        is_verified=True,
        password="x",
    )


@pytest.fixture
def vendor(vendor_user, city, service):
    v = Vendor.objects.create(
        user=vendor_user,
        business_name="نورنگار چت",
        slug="noornegar-chat",
        city=city,
        phone="09122220001",
        verification_status=VerificationStatus.APPROVED,
        is_active=True,
    )
    v.services.add(service)
    return v


@pytest.fixture
def project_request(customer, city, service):
    req = ProjectRequest.objects.create(
        customer=customer,
        title="تابلو نئون تست چت",
        service=service,
        city=city,
        width_cm=200,
        height_cm=60,
        lighting_type=LightingType.LED,
        status=RequestStatus.DRAFT,
    )
    return submit_project_request(project_request=req)


@pytest.fixture
def quote(vendor, project_request):
    return create_quote(
        vendor=vendor,
        project_request=project_request,
        price=5_000_000,
        estimated_delivery_days=5,
        description="پیشنهاد تست",
    )


def _session_cookie_for(user) -> str:
    from django.contrib.auth import (
        BACKEND_SESSION_KEY,
        HASH_SESSION_KEY,
        SESSION_KEY,
    )
    from django.contrib.sessions.backends.db import SessionStore

    store = SessionStore()
    store[SESSION_KEY] = str(user.pk)
    store[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    store[HASH_SESSION_KEY] = user.get_session_auth_hash()
    store.save()
    return store.session_key


@pytest.mark.django_db
def test_open_chat_after_quote_shortlists(quote, customer):
    conversation = get_or_open_conversation(quote=quote, user=customer)
    quote.refresh_from_db()
    quote.request.refresh_from_db()
    assert conversation.status == ConversationStatus.OPEN
    assert quote.status == QuoteStatus.SHORTLISTED
    assert quote.request.status == RequestStatus.NEGOTIATING


@pytest.mark.django_db
def test_outsider_cannot_open_chat(quote, outsider):
    with pytest.raises(PermissionDenied):
        get_or_open_conversation(quote=quote, user=outsider)


@pytest.mark.django_db
def test_send_message_and_unread(quote, customer, vendor_user):
    send_message(quote=quote, user=customer, body="سلام، عکس سردر دارم")
    conversation = Conversation.objects.get(quote=quote)
    msg = conversation.messages.get()
    assert msg.body.startswith("سلام")
    assert msg.read_at is None

    send_message(quote=quote, user=vendor_user, body="بفرستید لطفاً")
    assert conversation.messages.count() == 2


@pytest.mark.django_db
def test_accept_closes_losing_conversations(
    customer, vendor, city, service, project_request
):
    quote_a = create_quote(
        vendor=vendor,
        project_request=project_request,
        price=4_000_000,
        estimated_delivery_days=4,
    )
    other_user = User.objects.create_user(
        username="09124440001",
        phone="09124440001",
        role=UserRole.VENDOR,
        is_verified=True,
        password="x",
    )
    other_vendor = Vendor.objects.create(
        user=other_user,
        business_name="رقیب چت",
        slug="raghib-chat",
        city=city,
        phone="09124440001",
        verification_status=VerificationStatus.APPROVED,
        is_active=True,
    )
    other_vendor.services.add(service)
    quote_b = create_quote(
        vendor=other_vendor,
        project_request=project_request,
        price=4_500_000,
        estimated_delivery_days=6,
    )
    get_or_open_conversation(quote=quote_a, user=customer)
    get_or_open_conversation(quote=quote_b, user=customer)
    send_message(quote=quote_b, user=customer, body="هنوز فکر می‌کنم")

    accept_quote(quote=quote_a, user=customer)

    conv_b = Conversation.objects.get(quote=quote_b)
    assert conv_b.status == ConversationStatus.CLOSED
    with pytest.raises(ChatError):
        send_message(quote=quote_b, user=customer, body="دیگر نباید برسد")


@pytest.mark.django_db
def test_customer_thread_page(client, customer, quote):
    client.force_login(customer)
    response = client.get(reverse("chat:thread", kwargs={"quote_id": quote.pk}))
    assert response.status_code == 200
    assert b"data-chat-thread" in response.content


@pytest.mark.django_db
def test_outsider_thread_forbidden(client, outsider, quote):
    client.force_login(outsider)
    response = client.get(reverse("chat:thread", kwargs={"quote_id": quote.pk}))
    assert response.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_websocket_connect_and_send(quote, customer):
    session_key = _session_cookie_for(customer)

    async def _run() -> None:
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{quote.pk}/",
            headers=[
                (b"cookie", f"sessionid={session_key}".encode()),
                (b"origin", b"http://testserver"),
                (b"host", b"testserver"),
            ],
        )
        connected, _ = await communicator.connect()
        assert connected

        ready = await communicator.receive_json_from()
        assert ready["type"] == "conversation.ready"

        await communicator.send_json_to(
            {"type": "message.send", "body": "سلام از سوکت"}
        )
        event = await communicator.receive_json_from()
        assert event["type"] == "message.new"
        assert event["message"]["body"] == "سلام از سوکت"

        await communicator.disconnect()

        count = await database_sync_to_async(
            lambda: Message.objects.filter(conversation__quote=quote).count()
        )()
        assert count == 1

    async_to_sync(_run)()


@pytest.mark.django_db(transaction=True)
def test_websocket_rejects_anonymous(quote):
    async def _run() -> None:
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chat/{quote.pk}/",
            headers=[
                (b"origin", b"http://testserver"),
                (b"host", b"testserver"),
            ],
        )
        connected, _code = await communicator.connect()
        assert connected is False

    async_to_sync(_run)()


@pytest.mark.django_db
def test_vendor_panel_exposes_unread_chat_count(customer, vendor, vendor_user, quote):
    from apps.vendors.panel import panel_context

    send_message(quote=quote, user=customer, body="سلام، موجود هستید؟")
    ctx = panel_context(vendor, "dashboard")
    assert ctx["unread_chat_count"] == 1

    conversation = Conversation.objects.get(quote=quote)
    from apps.chat.services import mark_read

    mark_read(conversation=conversation, user=vendor_user)
    ctx2 = panel_context(vendor, "chats")
    assert ctx2["unread_chat_count"] == 0


@pytest.mark.django_db
def test_vendor_cannot_open_conversation(quote, vendor_user):
    with pytest.raises(ChatError, match="مشتری"):
        get_or_open_conversation(quote=quote, user=vendor_user)
    assert not Conversation.objects.filter(quote=quote).exists()


@pytest.mark.django_db
def test_vendor_can_join_after_customer_opens(quote, customer, vendor_user):
    get_or_open_conversation(quote=quote, user=customer)
    conversation = get_or_open_conversation(quote=quote, user=vendor_user)
    assert conversation.quote_id == quote.pk


@pytest.mark.django_db
def test_vendor_cannot_send_before_customer_starts(quote, vendor_user):
    with pytest.raises(ChatError, match="مشتری"):
        send_message(quote=quote, user=vendor_user, body="سلام از تابلوساز")
    assert not Conversation.objects.filter(quote=quote).exists()


@pytest.mark.django_db
def test_vendor_thread_redirects_before_customer_starts(client, vendor_user, quote):
    client.force_login(vendor_user)
    response = client.get(reverse("chat:thread", kwargs={"quote_id": quote.pk}))
    assert response.status_code == 302
    assert response.url == reverse("vendors:my_quotes")
