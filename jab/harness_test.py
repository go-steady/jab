import asyncio
from typing_extensions import Protocol

import pytest
import jab


class NumberProvider(Protocol):
    def provide_number(self) -> int:
        pass


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
        pass


class ConcreteNumber:
    def __init__(self) -> None:
        pass

    def provide_number(self) -> int:
        return 5


class ClassNew:
    def __init__(self, t: ClassBasic) -> None:
        self.t = t

    async def on_start(self) -> None:
        print(self.t.get_thing())
        await asyncio.sleep(10)

    def on_stop(self) -> None:
        print("shutting down")


class MissingAnnotations:
    def __init__(self, name, age):  # type: ignore
        self.name = name
        self.age = age

    def who_am_i(self):  # type: ignore
        return "You Are {}. Age {}.".format(self.name, self.age)


def test_harness() -> None:
    app = jab.Harness().provide(ClassNew, ClassBasic, ConcreteNumber)
    assert app._env["ClassNew"].t is app._env["ClassBasic"]
    assert app._env["ClassBasic"].get_thing() == "Hello, 5!"


def test_on_start() -> None:
    jab.Harness().provide(ClassNew, ClassBasic, ConcreteNumber).run()


def test_no_annotation() -> None:
    with pytest.raises(jab.Exceptions.NoAnnotation):
        jab.Harness().provide(MissingAnnotations)
