from dataclasses import dataclass


@dataclass
class Person:
    first_names: list[str] = None
    initials: str = None
    surname: str = None
