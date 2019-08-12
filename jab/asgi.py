from typing import Any, Awaitable, Callable, Dict

from typing_extensions import Protocol

Receive = Callable[[], Awaitable[Dict[str, Any]]]
Send = Callable[[Dict[str, Any]], Awaitable[None]]
Handler = Callable[[Receive, Send], Awaitable[None]]


class EventHandler(Protocol):
    async def asgi(self, scope: Dict[str, str], receive: Receive, send: Send) -> None:
        pass


class NoopHandler:
    async def asgi(self, scope: Dict[str, str], receive: Receive, send: Send) -> None:
        pass
