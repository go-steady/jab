# 💉  jab ![py-version](https://img.shields.io/badge/python-3.7-blue.svg) ![codecov](https://img.shields.io/badge/coverage-90%25-green.svg)
###### A Python Dependency Injection Framework

`jab` is heavily inspired by [uber-go/fx](https://github.com/uber-go/fx).

Using the type annotations of classes' `__init__` functions, `jab` creates a dependency graph of the provided functions. When `provide` is called, the dependency graph is topologically sorted and each class is instantiated in the appropriate order with necessary dependencies being passed to each class's constructor method.

## Usage
### Example
```python
from typing_extensions import Protocol
from jab import Harness


class FreeClass:

    def __init__(self) -> None:
        self.name = "Steady"


class DependentClass:

    def __init__(self, fc: FreeClass) -> None:
        self.fc = fc


class Thinger(Protocol):
    def thing(self) -> str:
        pass


class ThingImplementer:

    def __init__(self) -> None:
        self._thing = "Anything"

    def thing(self) -> str:
        return self._thing


class ProtocolDependentClass:

    def __init__(self, t: Thinger, fc: FreeClass) -> None:
        self.t = t
        self.fc = fc

    async def run(self) -> None:
        print(self.t.thing())
        print(self.fc.name)


Harness().provide(ProtocolDependentClass,
                  ThingImplementer,
                  FreeClass,
                  DependentClass).run()
```

The above code would print the following to stdout:

```
Anything
Steady
```

## Lifecycle Methods

`jab` has three special lifecycle methods, `on_start`, `run`, and `on_stop`. Both `on_start` and `run` _must_ be async methods.

### on_start

When `run` is called on a jab harness it moves through three states, the first of which is `on_start`. The harness iterates through all of the objects included in the `provide` call, any object that has an `on_start` method is called. The main routine of the harness blocks until all `on_start` methods have completed. `on_start` methods are the only `jab` lifecycle methods that can take arguments. Any arguments passed into an `on_start` method must be provided to the harness as you would any other dependency.

### run

After the `on_start` methods have been called, the harness iterates throguh the objects again and calls all `run` methods simultaneously. Again the main routine blocks until all `run` methods have completed.

### on_stop

After all `run` methods have completed, the harness interates through all of the objects and looks for `on_stop` methods. Unlike `on_start` and `run`, `on_stop` can be either synchronous or asynchronously defined. The `on_stop` methods are called serially.

## Constructors

Currently `jab` only supports full class definitions in the `provide` call. It's planned to incorporate functional consturctors alongside class constructors.
