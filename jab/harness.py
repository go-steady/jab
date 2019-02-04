from __future__ import annotations

import asyncio
from copy import deepcopy
from inspect import isclass, isfunction, iscoroutinefunction
from typing import Any, Dict, Optional, List

import toposort
from typing_extensions import Protocol, _get_protocol_attrs  # type: ignore

from jab.exceptions import NoAnnotation, NoConstructor


class Harness:
    def __init__(self) -> None:
        self._provided: Dict[str, Any] = {}
        self._dep_graph: Dict[Any, Dict[str, Any]] = {}
        self._env: Dict[str, Any] = {}
        self._exec_order: List[str] = []

    def provide(self, *args: Any) -> Harness:  # NOQA
        for arg in args:
            self._check_provide(arg)
            self._provided[arg.__name__] = arg
        self._build_graph()

        return self

    def _build_graph(self) -> None:
        for name, obj in self._provided.items():
            dependencies = deepcopy(obj.__init__.__annotations__)

            if len(dependencies) < 1:
                raise NoAnnotation("{} is missing a type-annotated constructor".format(name))

            del dependencies["return"]

            concrete = {}

            for key, dep in dependencies.items():
                if issubclass(dep, Protocol):  # type: ignore
                    match = self._search_protocol(dep)
                    if match is None:
                        # XXX: Write an actual exception
                        raise Exception
                else:
                    match = self._search_concrete(dep)
                    if match is None:
                        # XXX: Write an actual exception
                        raise Exception

                concrete[key] = match
            self._dep_graph[name] = concrete

        self._build_env()

    def _build_env(self) -> None:
        deps = {}

        for k, v in self._dep_graph.items():
            deps[k] = {i for _, i in v.items()}

        execution_order = toposort.toposort_flatten(deps)
        self._exec_order = execution_order
        for x in execution_order:
            reqs = self._dep_graph[x]
            provided = {k: self._env[v] for k, v in reqs.items()}
            self._env[x] = self._provided[x](**provided)

    def _search_protocol(self, dep: Any) -> Optional[str]:
        for name, obj in self._provided.items():
            if isimplementation(obj, dep):
                return name
        return None

    def _search_concrete(self, dep: Any) -> Optional[str]:
        for name, obj in self._provided.items():
            if obj.__module__ == dep.__module__ and obj.__name__ == dep.__name__:
                return name
        return None

    def _check_provide(self, arg: Any) -> None:
        if not isclass(arg):
            raise NoConstructor(
                "Provided argument '{}' does not have a constructor function".format(
                    str(arg)
                )
            )

        try:
            arg.__init__.__annotations__
        except AttributeError:
            raise NoAnnotation(
                "Provided argument '{}' does not have a type-annotated constructor".format(
                    arg.__name__
                )
            )

    def run(self) -> None:
        aws = []
        for x in self._exec_order:
            try:
                if not iscoroutinefunction(self._provided[x].on_start):
                    raise Exception
                aws.append(self._env[x].on_start())
            except AttributeError:
                pass

        print(aws)
        try:
            asyncio.get_event_loop().run_until_complete(asyncio.gather(*aws))
        except KeyboardInterrupt:
            print("goodbye")
        except Exception as e:
            print(str(e))

        for x in self._exec_order[::-1]:
            try:
                fn = self._env[x].on_stop
                if iscoroutinefunction(fn):
                    asyncio.get_event_loop().run_until_complete(fn())
                else:
                    fn()
            except AttributeError:
                pass


def isimplementation(cls_: Any, proto: Any) -> bool:
    proto_annotations: Dict[str, Any] = {}
    cls_annotations: Dict[str, Any] = {}

    if hasattr(proto, "__annotations__"):

        if not hasattr(cls_, "__annotations__"):
            return False

        proto_annotations = proto.__annotations__  # type: ignore
        cls_annotations = cls_.__annotations__

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
            proto_signature = proto_concrete.__annotations__

            try:
                cls_signature = cls_concrete.__annotations__
            except AttributeError:
                return False

            if proto_signature != cls_signature:
                return False

            continue

        if cls_concrete != proto_concrete:
            return False

    return True
