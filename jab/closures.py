from typing import Callable, Type, TypeVar


T = TypeVar("T")


def closure(cls_: Type[T]) -> Type[T]:
    """
    `closure` provides a decorator for adding a `jab` property method to a class
    as well as for ensuring that multiple instances of that class can be provided
    to the jab harness by ensuring a unique `_jab` attribute id for each instance.
    """

    def _closure(self: Type[T]) -> Callable[[], Type[T]]:
        ident = f"{type(self).__name__}-{id(self)}"
        self.__setattr__("_jab", ident)  # type: ignore

        def inner() -> Type[T]:
            return self

        inner.__annotations__["return"] = type(self)
        return inner

    setattr(cls_, "jab", property(_closure))
    return cls_
