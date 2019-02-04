import asyncio

import pytest
import toposort
from typing_extensions import Protocol

import jab


class NumberProvider(Protocol):
    def provide_number(self) -> int:
        pass  # pragma: no cover


class ClassBasic:
    number: int

    def __init__(self, n: NumberProvider) -> None:
        self.number: int = n.provide_number()

    def get_thing(self) -> str:
        return "Hello, {}!".format(self.number)

    async def on_start(self) -> None:
        await asyncio.sleep(1)
        print("Class Basic Getting Called")


class Thing(Protocol):
    number: int

    def get_thing(self) -> str:
        pass  # pragma: no cover


class ConcreteNumber:
    def __init__(self) -> None:
        pass

    def provide_number(self) -> int:
        return 5

    async def run(self) -> None:
        await asyncio.sleep(1)
        print("concrete")


class ClassNew:
    def __init__(self, t: ClassBasic) -> None:
        self.t = t

    async def run(self) -> None:
        print(self.t.get_thing())
        await asyncio.sleep(3)
        print("waited and came back")

    def on_stop(self) -> None:
        print("shutting down")


class MissingAnnotations:
    def __init__(self, name, age):  # type: ignore
        self.name = name  # pragma: no cover
        self.age = age  # pragma: no cover

    def who_am_i(self):  # type: ignore
        return "You Are {}. Age {}.".format(self.name, self.age)  # pragma: no cover


class BadOnStart:
    def __init__(self) -> None:
        self.name = "bad"  # pragma: no cover

    def on_start(self) -> None:
        pass  # pragma: no cover


class BadRun:
    def __init__(self) -> None:
        self.name = "bad"  # pragma: no cover

    def run(self) -> None:
        pass  # pragma: no cover


class Twoer(Protocol):
    def two(self) -> str:
        pass  # pragma: no cover


class CircleOne:
    def __init__(self, c: Twoer) -> None:
        pass  # pragma: no cover


class CircleTwo:
    def __init__(self, c: CircleOne) -> None:
        pass  # pragma: no cover

    def two(self) -> str:
        return "Two"  # pragma: no cover


def test_harness() -> None:
    app = jab.Harness().provide(ClassNew, ClassBasic, ConcreteNumber)
    assert app._env["ClassNew"].t is app._env["ClassBasic"]
    assert app._env["ClassBasic"].get_thing() == "Hello, 5!"


def test_no_annotation() -> None:
    with pytest.raises(jab.Exceptions.NoAnnotation):
        jab.Harness().provide(MissingAnnotations)


def test_missing_dep() -> None:
    with pytest.raises(jab.Exceptions.MissingDependency):
        jab.Harness().provide(ClassNew)


def test_sync_on_start() -> None:
    with pytest.raises(jab.Exceptions.InvalidLifecycleMethod):
        jab.Harness().provide(BadOnStart).run()


def test_sync_run() -> None:
    with pytest.raises(jab.Exceptions.InvalidLifecycleMethod):
        jab.Harness().provide(BadRun).run()


def test_circular_dependency() -> None:
    with pytest.raises(toposort.CircularDependencyError):
        jab.Harness().provide(CircleOne, CircleTwo)


def test_missing_protocol() -> None:
    with pytest.raises(jab.Exceptions.MissingDependency):
        jab.Harness().provide(CircleOne)


def test_non_class_provide() -> None:
    with pytest.raises(jab.Exceptions.NoConstructor):
        jab.Harness().provide("niels")


def test_on_start() -> None:
    jab.Harness().provide(ClassNew, ClassBasic, ConcreteNumber).run()
