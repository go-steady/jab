from dataclasses import dataclass, field
from typing import Any, List


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
