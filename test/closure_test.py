from inspect import isfunction
from typing import get_type_hints

import pytest

import jab
from dataclasses import dataclass


@jab.closure
class SampleClass:
    def __init__(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name


def test_closure_func():
    t = SampleClass("stntngo")
    assert isfunction(t.jab)


def test_closure_return():
    u = SampleClass("stntngo")
    assert get_type_hints(u.jab)["return"] == SampleClass


def test_closure_pass():
    v = SampleClass("stntngo")
    s = v.jab()

    assert s.get_name() == "stntngo"
    assert s is v


def test_closure_jab_flag():
    a = SampleClass("stntngo")
    b = a.jab()

    x = SampleClass("stntngo")
    y = x.jab()

    assert b._jab != y._jab
    assert b is not y

    with pytest.raises(jab.Exceptions.DuplicateProvide):
        jab.Harness().provide(y.jab, y.jab)


def test_play_well_with_others():
    @jab.closure
    @dataclass
    class User:
        name: str
        email: str
        password: str

    user_one = User(name="Dave", email="hal@9000.net", password="imsorry")

    assert user_one is user_one.jab()
    assert user_one.name == "Dave"
