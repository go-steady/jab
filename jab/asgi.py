from typing import Awaitable, Callable

Receive = Callable[[None], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]
Handler = Callable[[Receive, Send], Awaitable[None]]
