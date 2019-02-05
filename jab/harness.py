from __future__ import annotations

import asyncio
from copy import deepcopy
from inspect import isclass, iscoroutinefunction, isfunction
from typing import Any, Dict, List, Optional

import toposort
from typing_extensions import Protocol, _get_protocol_attrs  # type: ignore

from jab.exceptions import (
    InvalidLifecycleMethod,
    MissingDependency,
    NoAnnotation,
    NoConstructor,
)
from jab.logging import DefaultJabLogger, Logger

DEFAULT_LOGGER = "DEFAULT LOGGER"


class Harness:
    """
    `Harness` takes care of the wiring of depdencies to constructors that grows tedious quickly.
    By providing class definitions to the provide method, the Harness will know how to wire up
    all the classes' dependencies so that everything is connected and run appropriately.
    """

    def __init__(self) -> None:
        self._provided: Dict[str, Any] = {}
        self._dep_graph: Dict[Any, Dict[str, Any]] = {}
        self._env: Dict[str, Any] = {}
        self._exec_order: List[str] = []
        self._loop = asyncio.get_event_loop()
        self._logger = DefaultJabLogger()

    def provide(self, *args: Any) -> Harness:  # NOQA
        """
        `provide` provides the Harness with the class definitions it is to construct, maintain,
        and run inside its local environment.

        Parameters
        ----------
        args : Any
            Each element of args must be a class definition with a type-annotated constructor.
        """
        for arg in args:
            self._check_provide(arg)
            name = arg.__name__

            if isfunction(arg):
                name = arg.__annotations__["return"].__name__

            self._provided[name] = arg
        self._build_graph()

        return self

    def _build_graph(self) -> None:
        """
        `_build_graph` builds the dependency graph based on the type annotations of the provided class
        constructors.

        Raises
        ------
        MissingDependency
            If a class's constructor requires a dependency that has not been provided. This exception
            will be raised.
        """
        for name, obj in self._provided.items():
            if isfunction(obj):
                dependencies = deepcopy(obj.__annotations__)
                name = dependencies["return"].__name__
            else:
                dependencies = deepcopy(obj.__init__.__annotations__)

            concrete = {}

            for key, dep in dependencies.items():
                if key == "return":
                    continue

                if issubclass(dep, Protocol):  # type: ignore
                    match = self._search_protocol(dep)
                    if match is None:
                        raise MissingDependency(
                            "Can't build depdencies for {}. Missing suitable argument for parameter {} [{}].".format(  # NOQA
                                name, key, str(dep)
                            )
                        )
                else:
                    match = self._search_concrete(dep)
                    if match is None:
                        raise MissingDependency(
                            "Can't build depdencies for {}. Missing suitable argument for parameter {} [{}].".format(  # NOQA
                                name, key, str(dep)
                            )
                        )

                concrete[key] = match
            self._dep_graph[name] = concrete

        self._build_env()

    def _build_env(self) -> None:
        """
        `build_env` takes the dependency graph and topologically sorts
        the Harness's dependencies and then constructs then in order,
        providing each constructor with the necessary constructed objects.

        Raises
        ------
        toposort.CircularDependencyError
            If a circular dependency exists in the provided objects this function
            will fail.
        """
        deps = {}

        for k, v in self._dep_graph.items():
            deps[k] = {i for _, i in v.items()}

        execution_order = toposort.toposort_flatten(deps)
        self._exec_order = execution_order
        for x in execution_order:

            if x == DEFAULT_LOGGER:
                continue

            reqs = self._dep_graph[x]
            provided = {k: self._env[v] for k, v in reqs.items()}
            self._env[x] = self._provided[x](**provided)

    def _search_protocol(self, dep: Any) -> Optional[str]:
        """
        `search_protocol` attempts to match a Protocol definition to an object
        provided to the Harness. If the required Protocol is that of `jab.Logger`
        and no suitable Logger has been provided, the `DefaultJabLogger` stored in
        `_logger` will be provided.

        Parameters
        ----------
        dep : Any
            The protocol that some object must implement.

        Returns
        -------
        Optional[str]
            If an object can be found that implements the provided Protocol, its key-value
            is returned, otherwise None is returned.
        """
        for name, obj in self._provided.items():
            if isfunction(obj):
                obj = obj.__annotations__["return"]

            if isimplementation(obj, dep):
                return name

        if dep is Logger:
            self._env[DEFAULT_LOGGER] = self._logger
            return DEFAULT_LOGGER

        return None

    def _search_concrete(self, dep: Any) -> Optional[str]:
        """
        `search_concrete` attempts to match a concrete class dependency to an object
        provided to the Harness.

        Parameters
        ----------
        dep : Any
            The class that must be found inside of the provided class list.

        Returns
        -------
        Optional[str]
            If the appropriate object can be found, its key-name is returned. If
            an appropriate object can't be found, None is returned.
        """
        for name, obj in self._provided.items():
            if isfunction(obj):
                obj = obj.__annotations__["return"]

            if obj.__module__ == dep.__module__ and obj.__name__ == dep.__name__:
                return name

        return None

    def _check_provide(self, arg: Any) -> None:
        """
        `check_provide` ensures that an argument to the provide function meets the requirements
        necessary to build and receive dependencies.

        Parameters
        ----------
        arg : Any
            Any sort of object that has been passed into `Harness.provide`

        Raises
        ------
        NoConstructor
            Raised with the object passed to provide is not a class definition.
        NoAnnotation
            Raised when the constructor function of the class definition lacks
            type annotations necessary for dependency wiring.
        """
        _is_func = False
        if not isclass(arg):
            if not isfunction(arg):
                raise NoConstructor(
                    "Provided argument '{}' does not have a constructor function".format(
                        str(arg)
                    )
                )
            else:
                _is_func = True
                deps = arg.__annotations__
                if len(deps) == 0 or deps.get("return") is None:
                    raise NoConstructor(
                        "Provided argument '{}' does not have a constructor function".format(
                            str(arg)
                        )
                    )

        try:
            if _is_func:
                deps = arg.__annotations__
            else:
                deps = arg.__init__.__annotations__

            if len(deps) == 0:
                raise NoAnnotation(
                    "Provided argument '{}' does not have a type-annotated constructor".format(
                        arg.__name__
                    )
                )
        except AttributeError:
            # This can't actually be reached in Python 3.7+ but
            # better safe than sorry.
            raise NoAnnotation(
                "Provided argument '{}' does not have a type-annotated constructor".format(
                    arg.__name__
                )  # pragma: no cover
            )

    def _on_start(self) -> bool:
        """
        `_on_start` gathers and calls all `on_start` methods of the provided objects.
        The futures of the `on_start` methods are collected and awaited inside of the
        Harness's event loop. `on_start` methods are the only methods that are allowed
        to take arguments. The paramters must be satisfied by the objects or classes
        passed into the Harness's `provide` function like a constructor.
        """
        start_awaits = []
        for x in self._exec_order:
            try:
                if not iscoroutinefunction(self._env[x].on_start):
                    raise InvalidLifecycleMethod(
                        "{}.on_start must be an async method".format(x)
                    )
                in_ = self._env[x].on_start.__annotations__

                map_ = {}
                for key, dep in in_.items():
                    if key == "return":
                        continue

                    if issubclass(dep, Protocol):  # type: ignore
                        match = self._search_protocol(dep)
                        if match is None:
                            raise MissingDependency(
                                "Can't build depdencies for {}'s on_start method. Missing suitable argument for parameter {} [{}].".format(  # NOQA
                                    x, key, str(dep)
                                )
                            )
                    else:
                        match = self._search_concrete(dep)
                        if match is None:
                            raise MissingDependency(
                                "Can't build depdencies for {}'s on_start method. Missing suitable argument for parameter {} [{}].".format(  # NOQA
                                    x, key, str(dep)
                                )
                            )

                    map_[key] = match

                kwargs = {k: self._env[v] for k, v in map_.items()}
                start_awaits.append(self._env[x].on_start(**kwargs))
                self._logger.debug("Added on_start method for {}".format(x))
            except AttributeError:
                pass

        try:
            self._logger.debug("Executing on_start methods.")
            self._loop.run_until_complete(asyncio.gather(*start_awaits))
        except KeyboardInterrupt:
            self._logger.critical(
                "Keyboard interrupt during execution of on_start methods."
            )
            return True
        except Exception as e:
            self._logger.critical(
                "Encountered an unexpected error during executing of on_start methods ({})".format(
                    str(e)
                )
            )
            return True

        return False

    def _on_stop(self) -> None:
        """
        `_on_stop` gathers and calls all `on_stop` methods of the provided objects.
        Unlike `_on_start` and `_run` it thee `on_stop` methods are called serially.
        """
        for x in self._exec_order[::-1]:
            try:
                fn = self._env[x].on_stop
                if iscoroutinefunction(fn):
                    self._loop.run_until_complete(fn())
                else:
                    fn()
                self._logger.debug("Executed on_stop method for {}".format(x))
            except AttributeError:
                pass

    def _run(self) -> None:
        """
        `_run` gathers and calls all `run` methods of the provided objects.
        These methods must be async and are run inside of a `gather` call.
        The main execution thread blocks until all of these `run` methods complete.
        """
        run_awaits = []
        for x in self._exec_order:
            try:
                if not iscoroutinefunction(self._env[x].run):
                    raise InvalidLifecycleMethod(
                        "{}.run must be an async method".format(x)
                    )
                run_awaits.append(self._env[x].run())
                self._logger.debug("Added run method for {}".format(x))
            except AttributeError:
                pass

        try:
            self._logger.debug("Executing run methods.")
            self._loop.run_until_complete(asyncio.gather(*run_awaits))
        except KeyboardInterrupt:
            self._logger.critical("Keyboard interrupt during execution of run methods.")
        except Exception as e:
            self._logger.critical(
                "Encountered unexpected error during execution of run methods ({})".format(
                    str(e)
                )
            )

    def run(self) -> None:
        """
        `run` executes the full lifecycle of the Harness. All `on_start` methods are executed, then all
        `run` methods, and finally all `on_stop` methods.
        """
        interrupt = self._on_start()

        if not interrupt:
            self._run()

        self._on_stop()


def isimplementation(cls_: Any, proto: Any) -> bool:
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
