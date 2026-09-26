from __future__ import annotations

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import PermissionDenied, ValidationError

from apps.chat.selectors import conversation_group_name, user_can_access_quote
from apps.chat.services import (
    ChatError,
    get_or_open_conversation,
    mark_read,
    send_message,
)
from apps.quotes.models import Quote

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    quote_id: int
    group_name: str
    conversation_id: int | None

    async def connect(self) -> None:
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return

        try:
            self.quote_id = int(self.scope["url_route"]["kwargs"]["quote_id"])
        except (KeyError, TypeError, ValueError):
            await self.close(code=4400)
            return

        quote = await self._get_quote(self.quote_id)
        if quote is None:
            await self.close(code=4404)
            return

        allowed = await self._can_access(quote, user)
        if not allowed:
            await self.close(code=4403)
            return

        try:
            conversation = await self._open(quote, user)
        except (PermissionDenied, ChatError):
            await self.close(code=4403)
            return

        self.conversation_id = conversation.pk
        self.group_name = conversation_group_name(self.quote_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "conversation.ready",
                    "conversation_id": conversation.pk,
                    "status": conversation.status,
                    "quote_id": self.quote_id,
                }
            )
        )

    async def disconnect(self, code: int) -> None:
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data: str | None = None, bytes_data=None) -> None:
        if not text_data:
            return
        user = self.scope["user"]
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error("validation", "پیام نامعتبر است.")
            return

        event_type = payload.get("type")
        if event_type == "message.send":
            await self._handle_send(user=user, body=str(payload.get("body") or ""))
            return
        if event_type == "message.read":
            await self._handle_read(user=user)
            return
        await self._send_error("validation", "نوع پیام پشتیبانی نمی‌شود.")

    async def chat_event(self, event: dict) -> None:
        await self.send(text_data=json.dumps(event["payload"]))

    async def _handle_send(self, *, user, body: str) -> None:
        try:
            await self._send_message(user=user, body=body)
        except ChatError as exc:
            await self._send_error(
                "closed" if "بسته" in str(exc) else "validation", str(exc)
            )
        except PermissionDenied:
            await self._send_error("forbidden", "دسترسی مجاز نیست.")
            await self.close(code=4403)
        except ValidationError as exc:
            await self._send_error("validation", str(exc))

    async def _handle_read(self, *, user) -> None:
        try:
            await self._mark_read(user=user)
        except PermissionDenied:
            await self._send_error("forbidden", "دسترسی مجاز نیست.")

    async def _send_error(self, code: str, message: str) -> None:
        await self.send(
            text_data=json.dumps({"type": "error", "code": code, "message": message})
        )

    @database_sync_to_async
    def _get_quote(self, quote_id: int) -> Quote | None:
        return (
            Quote.objects.select_related("request", "vendor", "vendor__user")
            .filter(pk=quote_id)
            .first()
        )

    @database_sync_to_async
    def _can_access(self, quote: Quote, user) -> bool:
        return user_can_access_quote(quote=quote, user=user)

    @database_sync_to_async
    def _open(self, quote: Quote, user):
        return get_or_open_conversation(quote=quote, user=user)

    @database_sync_to_async
    def _send_message(self, *, user, body: str):
        quote = Quote.objects.select_related("request", "vendor", "vendor__user").get(
            pk=self.quote_id
        )
        return send_message(quote=quote, user=user, body=body)

    @database_sync_to_async
    def _mark_read(self, *, user) -> int:
        from apps.chat.models import Conversation

        conversation = Conversation.objects.select_related("quote").get(
            quote_id=self.quote_id
        )
        return mark_read(conversation=conversation, user=user)
