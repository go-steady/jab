from typing_extensions import Protocol

from .harness import Harness


class NumberProvider(Protocol):
    def provide_number(self) -> int:
        pass


class ClassBasic:
    number: int

    def __init__(self, n: NumberProvider) -> None:
        self.number: int = n.provide_number()

    def get_thing(self) -> str:
        return "Hello, {}!".format(self.number)


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


def test_harness() -> None:
    app = Harness().provide(ClassNew, ClassBasic, ConcreteNumber)
    assert app._env["ClassNew"].t is app._env["ClassBasic"]
    assert app._env["ClassBasic"].get_thing() == "Hello, 5!"
