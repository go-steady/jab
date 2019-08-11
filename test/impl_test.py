from typing_extensions import Protocol

import pytest

from jab.search import isimplementation


@pytest.fixture()
def protocol():
    class Stringer(Protocol):
        def string(self) -> str:
            pass

    class StringerProvider(Protocol):
        def provide_stringer(self) -> Stringer:
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

        def provide_stringer(self) -> StringerImpl:
            return self._stringer

    return Implementation


def test_protocol_returning_protocol(protocol, impl):
    assert isimplementation(impl, protocol)
