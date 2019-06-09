import asyncio
from collections import Counter
from inspect import isfunction
from typing import get_type_hints

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


class NeedsLogger:
    def __init__(self, l: jab.Logger) -> None:
        self.log = l  # pragma: no cover


class ArgedOnStart:
    def __init__(self) -> None:
        pass

    async def on_start(self, thing: Thing) -> None:
        print(thing.get_thing())


def ProvideCounter() -> Counter:
    return Counter()


class NeedsCounter:
    def __init__(self, c: Counter) -> None:
        self.c = c
        self.c["test"] += 2


class Shouter(Protocol):
    def shout(self) -> str:
        pass


class ImplementsShout:
    def __init__(self, word: str) -> None:
        self.word = word

    def shout(self) -> str:
        return self.word.upper()


def ProvidesShouter() -> ImplementsShout:
    return ImplementsShout("hello")


class NeedsShouter:
    def __init__(self, s: Shouter) -> None:
        self.s = s

    async def run(self) -> None:
        print(self.s.shout())


def FunctionalRequire(c: Counter) -> NeedsCounter:
    return NeedsCounter(c)


def test_harness() -> None:
    app = jab.Harness().provide(ClassNew, ClassBasic, ConcreteNumber)
    app.build()
    assert app._env["ClassNew"].t is app._env["ClassBasic"]
    assert app._env["ClassBasic"].get_thing() == "Hello, 5!"


def test_no_annotation() -> None:
    with pytest.raises(jab.Exceptions.NoAnnotation):
        jab.Harness().provide(MissingAnnotations)


def test_missing_dep() -> None:
    with pytest.raises(jab.Exceptions.MissingDependency):
        jab.Harness().provide(ClassNew).build()


def test_sync_run() -> None:
    with pytest.raises(jab.Exceptions.InvalidLifecycleMethod):
        jab.Harness().provide(BadRun).run()


def test_circular_dependency() -> None:
    with pytest.raises(toposort.CircularDependencyError):
        jab.Harness().provide(CircleOne, CircleTwo).build()


def test_missing_protocol() -> None:
    with pytest.raises(jab.Exceptions.MissingDependency):
        jab.Harness().provide(CircleOne).build()


def test_non_class_provide() -> None:
    with pytest.raises(jab.Exceptions.NoConstructor):
        jab.Harness().provide("niels")


def test_on_start() -> None:
    jab.Harness().provide(ClassNew, ClassBasic, ConcreteNumber).run()


def test_logger() -> None:
    harness = jab.Harness().provide(NeedsLogger)
    harness.build()
    assert harness._env["NeedsLogger"].log is harness._logger


def test_arugments_in_on_start() -> None:
    with pytest.raises(jab.Exceptions.MissingDependency):
        jab.Harness().provide(ArgedOnStart).run()

    jab.Harness().provide(ArgedOnStart, ClassBasic, ConcreteNumber).run()


def test_functional_constructor() -> None:
    h = jab.Harness().provide(ProvideCounter, NeedsCounter)
    h.build()
    assert h._env["Counter"] is h._env["NeedsCounter"].c
    assert h._env["Counter"]["test"] == 2


def test_concrete_function_protocol_need() -> None:
    h = jab.Harness().provide(NeedsShouter, ProvidesShouter)
    h.build()
    assert h._env["NeedsShouter"].s.shout() == "HELLO"


def test_functional_requires() -> None:
    jab.Harness().provide(FunctionalRequire, ProvideCounter)


def test_bad_function() -> None:
    def bad_func():  # type: ignore
        return None

    with pytest.raises(jab.Exceptions.NoConstructor):
        jab.Harness().provide(bad_func, NeedsCounter)


def test_inspect() -> None:
    h = jab.Harness().provide(
        ProvideCounter, NeedsCounter, NeedsShouter, ProvidesShouter
    )

    h.build()

    for x in h.inspect():
        assert x == h.inspect(x.constructor)

        if isfunction(x.constructor):
            hints = get_type_hints(x.constructor)
        else:
            hints = get_type_hints(x.constructor.__init__)

        assert len([x for x in hints.keys() if x != "return"]) == len(x.dependencies)
