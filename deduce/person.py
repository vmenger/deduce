from dataclasses import dataclass
from typing import Optional


@dataclass
class Person:
    first_names: Optional[list[str]] = None
    initials: Optional[str] = None
    surname: Optional[str] = None
