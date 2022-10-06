import re
import warnings

import docdeid
from docdeid.annotate.annotation_processor import OverlapResolver
from rapidfuzz.distance import DamerauLevenshtein

from deduce.annotate.annotate import Person, get_doc_processors, tokenizer
from deduce.annotate.annotation_processing import DeduceMergeAdjacentAnnotations
from deduce.annotate.redact import DeduceRedactor

warnings.simplefilter(action="once")


class Deduce(docdeid.DocDeid):
    def __init__(self):
        super().__init__()
        self._initialize_deduce()

    def _initialize_deduce(self):

        self.tokenizers["default"] = tokenizer

        for name, processor in get_doc_processors().items():
            self.processors[name] = processor

        self.processors["overlap_resolver"] = OverlapResolver(
            sort_by=["length"], sort_by_callbacks={"length": lambda x: -x}
        )

        self.processors["merge_adjacent_annotations"] = DeduceMergeAdjacentAnnotations(
            slack_regexp=r"[\.\s\-,]?[\.\s]?"
        )

        self.processors["redactor"] = DeduceRedactor()


def annotate_intext(text: str, annotations: list[docdeid.Annotation]) -> str:
    """TODO This should go somewhere else, not sure yet."""

    annotations = sorted(
        list(annotations),
        key=lambda a: a.get_sort_key(by=["end_char"], callbacks={"end_char": lambda x: -x}),
    )

    for annotation in annotations:
        text = (
            f"{text[:annotation.start_char]}"
            f"<{annotation.tag.upper()}>{annotation.text}</{annotation.tag.upper()}>"
            f"{text[annotation.end_char:]}"
        )

    return text


# Backwards compatibility stuff beneath this line.

deduce_model = Deduce()


def _annotate_text_backwardscompat(
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

    text = "" or text

    if patient_first_names:
        patient_first_names = patient_first_names.split(" ")

    metadata = {
        "patient": Person(
            first_names=patient_first_names or None,
            initials=patient_initials or None,
            surname=patient_surname or None,
            given_name=patient_given_name or None,
        )
    }

    processors_enabled = []

    if names:
        processors_enabled += ["name_group"]
        processors_enabled += [
            "prefix_with_name",
            "interfix_with_name",
            "initial_with_capital",
            "initial_interfix",
            "first_name_lookup",
            "surname_lookup",
            "person_first_name",
            "person_initial_from_name",
            "person_initials",
            "person_given_name",
            "person_surname",
        ]
        processors_enabled += ["person_annotation_converter", "name_context"]

    if institutions:
        processors_enabled += ["institution", "altrecht"]

    if locations:
        processors_enabled += [
            "residence",
            "street_with_number",
            "postal_code",
            "postbus",
        ]

    if phone_numbers:
        processors_enabled += ["phone_1", "phone_2", "phone_3"]

    if patient_numbers:
        processors_enabled += ["patient_number"]

    if dates:
        processors_enabled += ["date_1", "date_2"]

    if ages:
        processors_enabled += ["age"]

    if urls:
        processors_enabled += ["email", "url_1", "url_2"]

    processors_enabled += ["overlap_resolver", "merge_adjacent_annotations", "redactor"]

    doc = deduce_model.deidentify(text=text, processors_enabled=processors_enabled, metadata=metadata)

    return doc


def annotate_text(text: str, *args, **kwargs):

    warnings.warn(
        message="The annotate_text function will disappear in a future version. "
        "Please use Deduce().deidenitfy(text) instead.",
        category=DeprecationWarning,
    )

    doc = _annotate_text_backwardscompat(text=text, *args, **kwargs)

    annotations = doc.annotations.sorted(by=["end_char"], callbacks={"end_char": lambda x: -x})

    for annotation in annotations:

        text = (
            f"{text[:annotation.start_char]}"
            f"<{annotation.tag.upper()} {annotation.text}>"
            f"{text[annotation.end_char:]}"
        )

    return text


def annotate_text_structured(text: str, *args, **kwargs) -> list[docdeid.Annotation]:

    warnings.warn(
        message="The annotate_text_structured function will disappear in a future version. "
        "Please use Deduce().deidenitfy(text) instead.",
        category=DeprecationWarning,
    )

    doc = _annotate_text_backwardscompat(text=text, *args, **kwargs)

    return list(doc.annotations)


def deidentify_annotations(text):

    warnings.warn(
        message="The deidentify_annotations function will disappear in a future version. "
        "Please use Deduce().deidenitfy(text) instead.",
        category=DeprecationWarning,
    )

    if not text:
        return text

    # Patient tags are always simply deidentified (because there is only one patient
    text = re.sub(r"<patient\s([^>]+)>", "<patient>", text)

    # For al the other types of tags
    for tagname in [
        "persoon",
        "locatie",
        "instelling",
        "datum",
        "leeftijd",
        "patientnummer",
        "telefoonnummer",
        "url",
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
