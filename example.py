from typing import Callable, Dict, List

from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse, text
from typing_extensions import Protocol

import jab


class API:
    def __init__(self) -> None:
        self._sanic = Sanic(__name__)

    def add_route(self, handler: Callable, uri: str, methods: List[str]) -> None:
        self._sanic.add_route(handler, uri, methods=methods)

    async def run(self) -> None:
        server = await self._sanic.create_server()
        await server.wait_closed()


class GetSetter(Protocol):
    def get(self, key: str) -> str:
        pass

    def set(self, key: str, value: str) -> None:
        pass


class RouteAdder(Protocol):
    def add_route(self, handler: Callable, uri: str, methods: List[str]) -> None:
        pass


class Routes:
    def __init__(self, db: GetSetter) -> None:
        self.db = db

    async def get_secret(self, request: Request, name: str) -> HTTPResponse:
        value = self.db.get(name)
        return text("Name: {} / Secret: {}".format(name, value))

    async def post_secret(self, request: Request) -> HTTPResponse:
        incoming = request.json
        self.db.set(incoming["name"], incoming["secret"])
        return text("Successfully wrote to DB")

    async def on_start(self, app: RouteAdder) -> None:
        app.add_route(self.get_secret, "/secret/<name>", ["GET"])
        app.add_route(self.post_secret, "/secret", ["POST"])


class Database:
    def __init__(self) -> None:
        self._internal: Dict[str, str] = {}

    def get(self, key: str) -> str:
        return self._internal.get(key, "unknown")

    def set(self, key: str, value: str) -> None:
        self._internal[key] = value


app = jab.Harness().provide(API, Database, Routes)
