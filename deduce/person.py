from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Person:
    """
    Contains information on a person.

    Usable in a document metadata, where annotators can access it for more accurate annotation.
    """

    first_names: Optional[list[str]] = None
    initials: Optional[str] = None
    surname: Optional[str] = None

    @classmethod
    def from_keywords(
        cls,
        patient_first_names: str = "",
        patient_initials: str = "",
        patient_surname: str = "",
        patient_given_name: str = "",
    ) -> Person:
        """
        Get a Person from keywords. Mainly used for compatibility with keyword as used in deduce<=1.0.8.

        Args:
            patient_first_names: The patient first names, separated by whitespace.
            patient_initials: The patient initials.
            patient_surname: The patient surname.
            patient_given_name: The patient given name.

        Returns:
            A Person object containing the patient information.
        """

        patient_first_names_lst = []

        if patient_first_names:
            patient_first_names_lst = patient_first_names.split(" ")

        if patient_given_name:
            patient_first_names_lst.append(patient_given_name)

        return cls(
            first_names=patient_first_names_lst or None,
            initials=patient_initials or None,
            surname=patient_surname or None,
        )
