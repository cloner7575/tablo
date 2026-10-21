from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from functools import wraps

from asgiref.sync import sync_to_async

from apps.integrations.auth import authenticate
from apps.integrations.models import Connection

bearer: ContextVar[str] = ContextVar('mcp_bearer')


def actor(write: bool = False) -> Connection:
    return authenticate(bearer.get(), 'vendor:write' if write else 'vendor:read')


def database_tool[**P, R](function: Callable[P, R]) -> Callable[P, Awaitable[R]]:
    """
    Run Django ORM work off the event loop, preserving the token context.
    """

    @wraps(function)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        return await sync_to_async(function, thread_sensitive=True)(*args, **kwargs)

    return wrapped
