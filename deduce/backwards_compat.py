"""
Backwards compatibility functionality in this module.

Use with caution, rather, migrate to the new interface (Deduce.deidentify()). This code will not be documented and/or
maintained.
"""

import re
from typing import Any

import docdeid
from rapidfuzz.distance import DamerauLevenshtein

from deduce.person import Person


class _BackwardsCompat:
    deduce_model = None

    @classmethod
    def set_deduce_model(cls, deduce_model: Any) -> None:
        """Backwards compat."""
        cls.deduce_model = deduce_model

    @classmethod
    def annotate_text_backwardscompat(
        cls,
        text: str,
        patient_first_names: str = "",
        patient_initials: str = "",
        patient_surname: str = "",
        patient_given_name: str = "",
        names: bool = True,
        institutions: bool = True,
        locations: bool = True,
        phone_numbers: bool = True,
        patient_numbers: bool = True,
        dates: bool = True,
        ages: bool = True,
        urls: bool = True,
    ) -> docdeid.Document:
        """Backwards compat."""

        text = "" or text

        metadata = {
            "patient": Person.from_keywords(
                patient_first_names=patient_first_names,
                patient_initials=patient_initials,
                patient_surname=patient_surname,
                patient_given_name=patient_given_name,
            )
        }

        enabled = []

        if names:
            enabled += ["names"]
            enabled += [
                "prefix_with_name",
                "interfix_with_name",
                "initial_with_capital",
                "initial_interfix",
                "first_name_lookup",
                "surname_lookup",
                "person_first_name",
                "person_initial_from_name",
                "person_initials",
                "person_surname",
            ]
            enabled += ["person_annotation_converter", "name_context"]

        if institutions:
            enabled += ["institutions", "institution", "altrecht"]

        if locations:
            enabled += [
                "locations",
                "residence",
                "street_with_number",
                "postal_code",
                "postbus",
            ]

        if phone_numbers:
            enabled += ["phone_numbers", "phone_1", "phone_2", "phone_3"]

        if patient_numbers:
            enabled += ["patient_numbers", "patient_number"]

        if dates:
            enabled += ["dates", "date_1", "date_2"]

        if ages:
            enabled += ["ages", "age"]

        if urls:
            enabled += ["urls", "email", "url_1", "url_2"]

        enabled += ["post_processing", "overlap_resolver", "merge_adjacent_annotations", "redactor"]

        doc = cls.deduce_model.deidentify(text=text, enabled=enabled, metadata=metadata)

        return doc


def annotate_text_backwardscompat(text: str, *args, **kwargs) -> str:
    """Backwards compat."""

    doc = _BackwardsCompat.annotate_text_backwardscompat(text=text, *args, **kwargs)

    annotations = doc.annotations.sorted(by=["end_char"], callbacks={"end_char": lambda x: -x})

    for annotation in annotations:

        text = (
            f"{text[:annotation.start_char]}"
            f"<{annotation.tag.upper()} {annotation.text}>"
            f"{text[annotation.end_char:]}"
        )

    return text


def annotate_text_structured_backwardscompat(text: str, *args, **kwargs) -> list[docdeid.Annotation]:
    """Backwards compat."""

    doc = _BackwardsCompat.annotate_text_backwardscompat(text=text, *args, **kwargs)

    return list(doc.annotations)


def deidentify_annotations_backwardscompat(text: str) -> str:
    """Backwards compat."""

    if not text:
        return text

    # Patient tags are always simply deidentified (because there is only one patient
    text = re.sub(r"<PATIENT\s([^>]+)>", "<PATIENT>", text)

    # For al the other types of tags
    for tagname in [
        "PERSOON",
        "LOCATIE",
        "INSTELLING",
        "DATUM",
        "LEEFTIJD",
        "PATIENTNUMMER",
        "TELEFOONNUMMER",
        "URL",
    ]:

        # Find all values that occur within this type of tag
        phi_values = re.findall("<" + tagname + r"\s([^>]+)>", text)
        next_phi_values = []

        # Count unique occurrences (fuzzy) of all values in tags
        dispenser = 1

        # Iterate over all the values in tags
        while len(phi_values) > 0:

            # Compute which other values have edit distance <=1 (fuzzy matching)
            # compared to this value
            thisval = phi_values[0]
            dist = [DamerauLevenshtein.distance(x, thisval, score_cutoff=1) <= 1 for x in phi_values[1:]]

            # Replace this occurrence with the appropriate number from dispenser
            text = text.replace(f"<{tagname} {thisval}>", f"<{tagname}-{dispenser}>")

            # For all other values
            for index, value in enumerate(dist):

                # If the value matches, replace it as well
                if value:
                    text = text.replace(
                        f"<{tagname} {phi_values[index + 1]}>",
                        f"<{tagname}-{str(dispenser)}>",
                    )

                # Otherwise, carry it to the next iteration
                else:
                    next_phi_values.append(phi_values[index + 1])

            # This is for the next iteration
            phi_values = next_phi_values
            next_phi_values = []
            dispenser += 1

    # Return text
    return text
