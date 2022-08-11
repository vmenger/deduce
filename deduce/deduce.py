"""
Deduce is the main module, from which the annotate and
deidentify_annotations() methods can be imported
"""

import re

import docdeid
from docdeid.annotation.annotation_processor import (
    LongestFirstOverlapResolver,
    MergeAdjacentAnnotations,
)
from docdeid.annotation.redactor import BaseRedactor, SimpleRedactor
from nltk.metrics import edit_distance

from deduce import utility
from deduce.annotate import (
    AddressAnnotator,
    AgeAnnotator,
    DateAnnotator,
    EmailAnnotator,
    InstitutionAnnotator,
    NamesAnnotator,
    NamesContextAnnotator,
    PatientNumerAnnotator,
    PhoneNumberAnnotator,
    PostalcodeAnnotator,
    ResidenceAnnotator,
    UrlAnnotator,
    tokenizer,
)
from deduce.exception import NestedTagsError

annotators = {
    "names": NamesAnnotator(),
    "names_context": NamesContextAnnotator(),
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


class DeduceRedactor(BaseRedactor):
    """
    A simple redactor that replaces an annotation by [CATEGORY-n], with n being a counter.
    """

    @staticmethod
    def _get_annotations_by_category(annotations: list[docdeid.Annotation], category: str):
        return [annotation for annotation in annotations if annotation.category == category]

    def redact(self, text: str, annotations: list[docdeid.Annotation]):
        # TODO Implement this according to the logic in deidentify_annotations()

        annotations = sorted(annotations, key=lambda x: x.end_char)
        annotations_to_replacement = {}

        other_annotations = []

        for annotation in annotations:

            if annotation.category == "PATIENT":
                annotations_to_replacement[annotation] = "<PATIENT>"

            else:
                other_annotations.append(annotation)

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

            annotations_subset = self._get_annotations_by_category(annotations, tagname)
            annotations_to_replacement_tag = {}
            dispenser = 1

            for annotation in annotations_subset:

                match = False

                # Check match with any
                for annotation_match in annotations_to_replacement_tag.keys():

                    if edit_distance(annotation.text, annotation_match.text) <= 1:
                        annotations_to_replacement_tag[annotation] = annotations_to_replacement_tag[annotation_match]
                        match = True
                        break

                if not match:
                    annotations_to_replacement_tag[annotation] = f"<{tagname}-{dispenser}>"
                    dispenser += 1

            annotations_to_replacement |= annotations_to_replacement_tag

        assert len(annotations_to_replacement) == len(annotations)

        sorted_annotations = sorted(annotations, key=lambda a: -a.end_char)

        for annotation in sorted_annotations:

            text = text[:annotation.start_char] + annotations_to_replacement[annotation] + text[annotation.end_char:]

        return text


class Deduce(docdeid.DocDeid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_deduce()

    def _initialize_deduce(self):

        self._tokenizer = tokenizer
        self._redactor = DeduceRedactor()

        for name, annotator in annotators.items():
            self.add_annotator(name, annotator)

        self.add_annotation_postprocessor(
            "overlap_resolver",
            LongestFirstOverlapResolver()
        )

        self.add_annotation_postprocessor(
            "merge_adjacent_annotations",
            MergeAdjacentAnnotations(slack_regexp="[\.\s\-,]?[\.\s]?"),
        )



def _initialize_deduce() -> docdeid.DocDeid:
    return Deduce()


deduce_model = _initialize_deduce()


def annotate_text(
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
):

    """
    This method annotates text based on the input that includes names of a patient,
    and a number of flags indicating which PHIs should be annotated
    """

    if not text:
        return text

    text = text.replace("<", "(").replace(">", ")")

    if names:

        text = annotators["names"].annotate_intext(
            text=text,
            patient_first_names=patient_first_names,
            patient_initials=patient_initials,
            patient_surname=patient_surname,
            patient_given_name=patient_given_name,
        )

        text = annotators["names_context"].annotate_intext(text=text)

        text = utility.flatten_text(text)

    if institutions:
        text = annotators["institutions"].annotate_intext(text)

    if locations:

        text = annotators["residences"].annotate_intext(text)
        text = annotators["addresses"].annotate_intext(text)
        text = annotators["postal_codes"].annotate_intext(text)

    if phone_numbers:
        text = annotators["phone_numbers"].annotate_intext(text)

    if patient_numbers:
        text = annotators["patient_numbers"].annotate_intext(text)

    if dates:
        text = annotators["dates"].annotate_intext(text)

    if ages:
        text = annotators["ages"].annotate_intext(text)

    if urls:
        text = annotators["emails"].annotate_intext(text)
        text = annotators["urls"].annotate_intext(text)

    text = utility.merge_adjacent_tags(text)

    if utility.has_nested_tags(text):
        text = utility.flatten_text_all_phi(text)

    return text


def annotate_text_structured(text: str, *args, **kwargs):
    """
    This method annotates text based on the input that includes names of a patient,
    and a number of flags indicating which PHIs should be annotated
    """
    annotated_text = annotate_text(text, *args, **kwargs)

    if utility.has_nested_tags(annotated_text):
        raise NestedTagsError("Text has nested tags")
    tags = utility.find_tags(annotated_text)
    first_non_whitespace_character_index = utility.get_first_non_whitespace(text)
    # utility.get_annotations does not handle nested tags, so make sure not to pass it text with nested tags
    # Also, utility.get_annotations assumes that all tags are listed in the order they appear in the text
    annotations = utility.get_annotations(
        annotated_text, tags, first_non_whitespace_character_index
    )

    # Check if there are any annotations whose start+end do not correspond to the text in the annotation
    mismatched_annotations = [
        ann for ann in annotations if text[ann.start_char : ann.end_char] != ann.text
    ]
    if len(mismatched_annotations) > 0:
        print(
            "WARNING:",
            len(mismatched_annotations),
            "annotations have texts that do not match the original text",
        )

    return annotations


def deidentify_annotations(text):
    """
    Deidentify the annotated tags - only makes sense if annotate() is used first -
    otherwise the normal text is simply returned
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
