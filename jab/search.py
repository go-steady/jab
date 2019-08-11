from inspect import isfunction
from typing import Type, Optional, get_type_hints

from typing_extensions import Protocol, _get_protocol_attrs  # type: ignore


def isimplementation(cls_: Optional[Type], proto: Type) -> bool:
    """
    `isimplementation` checks to see if a provided class definition implement a provided Protocol definition.

    Parameters
    ----------
    cls_ : Any
        A concrete class defintiion
    proto : Any
        A protocol definition

    Returns
    -------
    bool
        Returns whether or not the provided class definition is a valid
        implementation of the provided Protocol.
    """
    if cls_ is None:
        return False

    proto_annotations = get_type_hints(proto)
    cls_annotations = get_type_hints(cls_)

    for attr in _get_protocol_attrs(proto):
        try:
            proto_concrete = getattr(proto, attr)
            cls_concrete = getattr(cls_, attr)
        except AttributeError:
            proto_concrete = proto_annotations.get(attr)
            cls_concrete = cls_annotations.get(attr)

        if cls_concrete is None:
            return False

        if isfunction(proto_concrete):
            proto_signature = get_type_hints(proto_concrete)

            try:
                cls_signature = get_type_hints(cls_concrete)
            except AttributeError:
                return False

            if issubclass(proto_signature.get("return"), Protocol):  # type: ignore
                proto_return: Type = proto_signature["return"]
                cls_return: Optional[Type] = cls_signature.get("return")
                if isimplementation(cls_return, proto_return):
                    cls_signature["return"] = proto_signature["return"]

            if proto_signature != cls_signature:
                return False

            continue

        if cls_concrete != proto_concrete:
            return False

    return True
