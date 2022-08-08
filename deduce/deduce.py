"""
Deduce is the main module, from which the annotate and
deidentify_annotations() methods can be imported
"""

import re

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
)
from deduce.exception import NestedTagsError


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

    # Replace < and > symbols
    text = text.replace("<", "(").replace(">", ")")

    if names:

        names_annotator = NamesAnnotator()
        names_context_annotator = NamesContextAnnotator()

        text = names_annotator.annotate_intext(
            text=text,
            patient_first_names=patient_first_names,
            patient_initials=patient_initials,
            patient_surname=patient_surname,
            patient_given_name=patient_given_name,
        )

        text = names_context_annotator.annotate_intext(text=text)

        text = utility.flatten_text(text)

    if institutions:
        institution_annotator = InstitutionAnnotator()
        text = institution_annotator.annotate_intext(text)

    if locations:

        residence_annotator = ResidenceAnnotator()
        address_annotator = AddressAnnotator()
        postalcode_annotator = PostalcodeAnnotator()

        text = residence_annotator.annotate_intext(text)
        text = address_annotator.annotate_intext(text)
        text = postalcode_annotator.annotate_intext(text)

    if phone_numbers:
        phone_number_annotator = PhoneNumberAnnotator()
        text = phone_number_annotator.annotate_intext(text)

    if patient_numbers:
        patient_number_annotator = PatientNumerAnnotator()
        text = patient_number_annotator.annotate_intext(text)

    if dates:
        date_annotator = DateAnnotator()
        text = date_annotator.annotate_intext(text)

    if ages:
        age_annotator = AgeAnnotator()
        text = age_annotator.annotate_intext(text)

    if urls:

        email_annotator = EmailAnnotator()
        url_annotator = UrlAnnotator()

        text = email_annotator.annotate_intext(text)
        text = url_annotator.annotate_intext(text)

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
        ann for ann in annotations if text[ann.start_ix : ann.end_ix] != ann.text_
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
