from typing import Any, Callable, Type

from typing_extensions import Protocol


class Instance(Protocol):
    def __setattr__(self, name: str, value: Any) -> None:
        pass


def closure(cls_: Type) -> Type:
    """
    `closure` provides a decorator for adding a `jab` property method to a class
    as well as for ensuring that multiple instances of that class can be provided
    to the jab harness by ensuring a unique `_jab` attribute id for each instance.
    """

    def _closure(self: Instance) -> Callable[[], Instance]:
        ident = f"{type(self).__name__}-{id(self)}"
        self.__setattr__("_jab", ident)

        def inner():
            return self

        inner.__annotations__["return"] = type(self)
        return inner

    setattr(cls_, "jab", property(_closure))
    return cls_
