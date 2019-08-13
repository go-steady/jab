from typing import overload, Union, List
from typing_extensions import Protocol, final

import pytest

from jab.search import isimplementation, ReturnedUnionType


@pytest.fixture()
def protocol():
    class Stringer(Protocol):
        def string(self) -> str:
            pass

    class StringerProvider(Protocol):
        def provide_stringer(self, ending: str) -> Stringer:
            pass

    return StringerProvider


@pytest.fixture()
def impl():
    class StringerImpl:
        def __init__(self, name: str) -> None:
            self._name = name

        def string(self) -> str:
            return self._name

    class Implementation:
        def __init__(self, stringer: StringerImpl) -> None:
            self._stringer = stringer

        def provide_stringer(self, ending: str) -> StringerImpl:
            return self._stringer

    return Implementation


def test_protocol_returning_protocol(protocol, impl):
    assert isimplementation(impl, protocol)


@pytest.fixture()
def impl_with_proto():
    class Stringer(Protocol):
        def string(self) -> str:
            pass

    class Implementation:
        def __init__(self, stringer: Stringer) -> None:
            self._stringer = stringer

        def provide_stringer(self, ending: str) -> Stringer:
            return self._stringer

    return Implementation


def test_impl_with_proto_return(protocol, impl_with_proto):
    assert isimplementation(impl_with_proto, protocol)


@pytest.fixture()
def overloaded():
    class Namer:
        def __init__(self, name) -> None:
            self._name = name

        def name(self) -> str:
            return self._name

    class Overloaded:
        def __init__(self) -> None:
            pass

        @overload
        def names(self, namers: List[Namer]) -> List[str]:
            pass

        @overload  # noqa: F811
        def names(self, namers: Namer) -> str:
            pass

        @final  # noqa: F811
        def names(self, namers: Union[List[Namer], Namer]) -> Union[List[str], str]:
            if isinstance(namers, Namer):
                return namers.name()

            return [x.name() for x in namers]

    class Names(Protocol):
        def names(self, namers: Namer) -> str:
            pass

    return (Overloaded, Names)


def test_good_overloaded(overloaded):
    Overloaded, Names = overloaded

    with pytest.raises(ReturnedUnionType):
        isimplementation(Overloaded, Names)


@pytest.fixture()
def bad_overloaded():
    class Namer:
        def __init__(self, name) -> None:
            self._name = name

        def name(self) -> str:
            return self._name

    class Overloaded:
        def __init__(self) -> None:
            pass

        @overload
        def names(self, namers: List[Namer]) -> List[str]:
            pass

        @overload  # noqa: F811
        def names(self, namers: Namer) -> str:
            pass

        @final  # noqa: F811
        def names(self, namers: Union[List[Namer], Namer]) -> Union[List[str], str]:
            if isinstance(namers, Namer):
                return [namers.name()]

            return namers[0].name()

    class Names(Protocol):
        def names(self, namers: Namer) -> str:
            pass

    return (Overloaded, Names)


def test_bad_overloaded(bad_overloaded):
    Overloaded, Names = bad_overloaded

    with pytest.raises(ReturnedUnionType):
        isimplementation(Overloaded, Names)


@pytest.fixture()
def missing_return():
    class MissingReturn:
        def __init__(self) -> None:
            pass

        def names(self, namers: str):
            return "name"

    class Other(Protocol):
        def other(self) -> int:
            pass

    class Names(Protocol):
        def names(self, namers: str) -> Other:
            pass

    return (MissingReturn, Names)


def test_missing_return(missing_return):
    MissingReturn, Names = missing_return

    assert not isimplementation(MissingReturn, Names)


@pytest.fixture()
def not_an_impl():
    class Impl:
        def __init__(self) -> None:
            pass

        def meth(self, n: int) -> float:
            return float(n ** 2)

    class Proto(Protocol):
        def meth(self, x: str) -> List[str]:
            pass

    return (Impl, Proto)


def test_not_an_impl(not_an_impl):
    Impl, Proto = not_an_impl
    assert not isimplementation(Impl, Proto)
