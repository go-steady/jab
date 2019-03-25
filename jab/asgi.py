from typing import Awaitable, Callable
from typing_extensions import Protocol

Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]
Handler = Callable[[Receive, Send], Awaitable[None]]


class EventHandler(Protocol):
    async def asgi(self, receive: Receive, send: Send) -> None:
        pass
