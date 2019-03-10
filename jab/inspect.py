from typing import Any, List

from dataclasses import dataclass, field


@dataclass
class Provided:
    name: str
    constructor: Any
    obj: Any
    dependencies: List["Dependency"] = field(default_factory=list)


@dataclass
class Dependency:
    parameter: str
    type: Any
    provided: Provided
