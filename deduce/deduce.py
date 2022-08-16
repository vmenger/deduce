import re

import docdeid
from docdeid.annotation.annotation_processor import (
    LongestFirstOverlapResolver,
    MergeAdjacentAnnotations,
)
from nltk.metrics import edit_distance

from deduce import utility
from deduce.annotate import (
    AddressAnnotator,
    AgeAnnotator,
    DateAnnotator,
    EmailAnnotator,
    InstitutionAnnotator,
    NamesAnnotator,
    PatientNumerAnnotator,
    PhoneNumberAnnotator,
    PostalcodeAnnotator,
    ResidenceAnnotator,
    UrlAnnotator,
    tokenizer,
)
from deduce.exception import NestedTagsError
from deduce.redact import DeduceRedactor

annotators = {
    "names": NamesAnnotator(flatten_function=utility.flatten_text),
    "institutions": InstitutionAnnotator(),
    "residences": ResidenceAnnotator(),
    "addresses": AddressAnnotator(),
    "postal_codes": PostalcodeAnnotator(),
    "phone_numbers": PhoneNumberAnnotator(),
    "patient_numbers": PatientNumerAnnotator(),
    "dates": DateAnnotator(),
    "ages": AgeAnnotator(),
    "emails": EmailAnnotator(),
    "urls": UrlAnnotator(),
}


class Deduce(docdeid.DocDeid):
    def __init__(self):
        super().__init__(tokenizer=tokenizer, redactor=DeduceRedactor())
        self._initialize_deduce()

    def _initialize_deduce(self):

        for name, annotator in annotators.items():
            self.add_annotator(name, annotator)

        self.add_annotation_postprocessor(
            "overlap_resolver", LongestFirstOverlapResolver()
        )

        self.add_annotation_postprocessor(
            "merge_adjacent_annotations",
            MergeAdjacentAnnotations(slack_regexp="[\.\s\-,]?[\.\s]?"),
        )


deduce_model = Deduce()


def annotate_text_backwardscompat(
    text,
    patient_first_names="",
    patient_initials="",
    patient_surname="",
    patient_given_name="",
    names=True,
    institutions=True,
    locations=True,
    phone_numbers=True,
    patient_numbers=True,
    dates=True,
    ages=True,
    urls=True,
) -> docdeid.Document:
    """Backwards compatibility only. Use Deduce().deidentify() instead."""

    text = "" or text

    text = text.replace("<", "(").replace(
        ">", ")"
    )  # Todo this must go in annotator_intext

    meta_data = {
        "patient_first_names": patient_first_names,
        "patient_initials": patient_initials,
        "patient_surname": patient_surname,
        "patient_given_name": patient_given_name,
    }

    annotators_enabled = []

    if names:
        annotators_enabled += ["names"]

    if institutions:
        annotators_enabled += ["institutions"]

    if locations:
        annotators_enabled += ["residences", "addresses", "postal_codes"]

    if phone_numbers:
        annotators_enabled += ["phone_numbers"]

    if patient_numbers:
        annotators_enabled += ["patient_numbers"]

    if dates:
        annotators_enabled += ["dates"]

    if ages:
        annotators_enabled += ["ages"]

    if urls:
        annotators_enabled += ["emails", "urls"]

    doc = deduce_model.deidentify(
        text=text, annotators_enabled=annotators_enabled, meta_data=meta_data
    )

    return doc


def annotate_text(text: str, *args, **kwargs):

    doc = annotate_text_backwardscompat(text=text, *args, **kwargs)
    text = doc.text

    annotations = list(sorted(doc.annotations, key=lambda a: -a.end_char))

    for annotation in annotations:
        text = f"{text[:annotation.start_char]}<{annotation.category.upper()} {annotation.text}>{text[annotation.end_char:]}"

    return text.strip()


def annotate_text_structured(text: str, *args, **kwargs) -> list[docdeid.Annotation]:

    doc = annotate_text_backwardscompat(text=text, *args, **kwargs)

    return list(doc.annotations)


def deidentify_annotations(text):
    """
    Deidentify the annotated tags - only makes sense if annotate() is used first.
    Backwards compatibility only. Use Deduce().deidentify() instead.
    """

    if not text:
        return text

    # Patient tags are always simply deidentified (because there is only one patient
    text = re.sub("<PATIENT\s([^>]+)>", "<PATIENT>", text)

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
            dist = [
                edit_distance(x, thisval, transpositions=True) <= 1
                for x in phi_values[1:]
            ]

            # Replace this occurrence with the appropriate number from dispenser
            text = text.replace(f"<{tagname} {thisval}>", f"<{tagname}-{dispenser}>")

            # For all other values
            for index, value in enumerate(dist):

                # If the value matches, replace it as well
                if dist[index]:
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
