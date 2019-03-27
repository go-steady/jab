# 💉  jab ![jab-version](https://img.shields.io/badge/version-0.3.0-orange.svg) ![py-version](https://img.shields.io/badge/python-3.7-blue.svg) ![codecov](https://img.shields.io/badge/coverage-83%25-yellowgreen.svg)
###### A Python Dependency Injection Framework

`jab` is heavily inspired by [uber-go/fx](https://github.com/uber-go/fx).

Using type annoted classes and functions, `jab` makes it easy to take advantage of Dependency Injection without any extra work. When a harness's `provide` method is called, all provided constructors will be wired together to produce a harness of instantiated objects with their appropriate dependencies.

## Usage
### Example
```python
from typing_extensions import Protocol

import jab


class FreeClass:

    def __init__(self) -> None:
        self.name = "World"


class DependentClass:

    def __init__(self, fc: FreeClass) -> None:
        self.fc = fc


class Thinger(Protocol):
    def thing(self) -> str:
        pass


class ThingImplementer:

    def __init__(self) -> None:
        self._thing = "Hello"

    def thing(self) -> str:
        return self._thing


class ProtocolDependentClass:

    def __init__(self, t: Thinger, fc: FreeClass) -> None:
        self.t = t
        self.fc = fc

    async def run(self) -> None:
    	print(f"{self.t.thing()}, {self.fc.name}!")


jab.Harness().provide(ProtocolDependentClass,
                  ThingImplementer,
                  FreeClass,
                  DependentClass).run()
```

The above code would print the following:

```
Hello, World!
```

### Constructors

Constructors come in two primary forms: Class Constructors and Functional Constructors.

#### Class Constructor
A Class constructor is the most common form of jab constructor. It is defined as you would any other class in python.

*Example*
```python
class Handler:
   def __init__(self, db: Database) -> None:
       self.db = db

   async def get_user(name: str) -> dict:
       return dict(self.db.query("select * from users where user = $1", name))
```

In the example above, the `Handler` class depends on a `Database` class which could be a Protocol or a concrete Class. If an object that satisfies the `Database` type is not passed into the harness's provide method along with the Handler class jab will fail to run.

#### Functional Constructor
A functional constructor on the other hand is not a class itself but is a free function that returns a class. Maybe you are doing this to provide a third party class with the necessary parameters already included insteaed of wrapping and method forwarding.

*Example*
```python
def provide_postgres() -> PostgresPool:
    pool = PostgresPool(dsn="postgres://localhost")
    return pool
```

Functional constructors can be extended to use closures to provide further utility. If we are defining the `PostgresPool` class from above we could instead do the following:

```python
class PostgresPool:
    def __init__(self, dsn: str) -> None:
    	self._jab = dsn
        self.dsn = dsn
	self.connection = self.connect()
    
    # <...>

    @property
    def jab(self) -> Callable:
        def inner() -> PostgresPool:
	   return self


pool = PostgresPool("postgres://localhost")

jab.Harness().provide(...other_deps, pool.jab).run()
```

Note the `_jab` attribute of PostgresPool from above. When defining a class that will have a closure constructor method and you are planning to provide multiple instances of the same class to the jab harness the `_jab` attribute will allow two instances of the same class to co-exist under different names so long as their `_jab` attributes are different.

### Lifecycle Methods

`jab` looks for three special lifecycle methods in provided classes, `on_start`, `run`, and `on_stop`. While `on_start` and `on_stop` can be either synchronous and async methods, `run` _must_ be an async method.

### on_start

When `run` is called on a jab harness it moves through three states, the first of which is `on_start`. The harness iterates through all of the objects in its internal environment and any object that has an `on_start` method has that method called. The main thread of the harness blocks until all `on_start` methods have completed. `on_start` methods are the only `jab` lifecycle methods that can take arguments. Any arguments passed into an `on_start` method must be provided to the harness as you would any other dependency. Like with instance instantiation, `on_start` methods will ensure that an `on_start` method's dependencies are called before it is called itself.

### run

After the `on_start` methods have been called, the harness iterates throguh the objects again and calls all `run` methods simultaneously. Again the main routine blocks until all `run` methods have completed.

### on_stop

After all `run` methods have completed, the harness interates through all of the objects and looks for `on_stop` methods. `on_stop` can be either synchronous or asynchronously defined. The `on_stop` methods are called serially with any asynchronous method effectively run synchronusly.
