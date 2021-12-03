"""
Deduce is the main module, from which the annotate and
deidentify_annotations() methods can be imported
"""

from deduce import utility
from .annotate import *
from .tokenizer import tokenize
from .utility import flatten_text, flatten_text_all_phi, to_text


class NestedTagsError(Exception):
    def __init__(self, msg: str):
        super().__init__(str)


def annotate_text(
    # The text to be annotated
    text,
    # First name
    patient_first_names="",
    # Initial
    patient_initials="",
    # Surname(s)
    patient_surname="",
    # Given name`
    patient_given_name="",
    # Person names, including initials
    names=True,
    # Geographical locations
    locations=True,
    # Institutions
    institutions=True,
    # Dates
    dates=True,
    # Ages
    ages=True,
    # Patient numbers
    patient_numbers=True,
    # Phone numbers
    phone_numbers=True,
    # Urls and e-mail addresses
    urls=True,
    # Debug option
    flatten=True,
):

    """
    This method annotates text based on the input that includes names of a patient,
    and a number of flags indicating which PHIs should be annotated
    """

    if not text:
        return text

    # Replace < and > symbols
    text = text.replace("<", "(")
    text = text.replace(">", ")")

    # Tokenize the text
    spans = tokenize(text)

    # Deidentify names
    if names:

        # First, based on the rules and lookup lists
        spans = annotate_names(
            spans,
            patient_first_names,
            patient_initials,
            patient_surname,
            patient_given_name,
        )

        # Then, based on the context
        spans = annotate_names_context(spans)

        # Flatten possible nested tags
        if flatten:
            spans = flatten_text(spans)

    # Institutions
    if institutions:
        spans = annotate_institution(spans)

    # Geographical locations
    if locations:
        spans = annotate_residence(spans)
        spans = annotate_address(text, spans)
        spans = annotate_postcode(text, spans)

    # Phone numbers
    if phone_numbers:
        spans = annotate_phone_number(text, spans)

    # Patient numbers
    if patient_numbers:
        spans = annotate_patient_number(text, spans)

    # Dates
    if dates:
        spans = annotate_date(text, spans)

    # Ages
    if ages:
        spans = annotate_age(text, spans)

    # Urls
    if urls:
        spans = annotate_email(text, spans)
        spans = annotate_url(text, spans)

    # Merge adjacent tags
    spans = merge_adjacent_tags(spans)

    annotations = [span for span in spans if span.is_annotation()]

    # Flatten tags
    if flatten and has_nested_tags(annotations):
        text = flatten_text_all_phi(text)

    # Return text
    return text


def get_adjacent_tags_replacement(match: re.Match) -> str:
    text = match.group(0)
    tag = match.group(1)
    left = match.group(2)
    right = match.group(3)
    start_ix = text.index(">") + 1
    end_ix = text[1:].index("<") + 1
    separator = text[start_ix:end_ix]
    return "<" + tag + " " + left + separator + right + ">"

def merge_adjacent_tags(spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """
    Adjacent tags are merged into a single tag
    :param spans: the spans containing the whole text, including annotations
    :return: the new list of spans containing the whole text, and merged annotations
    """
    end_ann_ix = None
    for i in range(len(spans)-1, -1, -1):
        token = spans[i]
        if not token.is_annotation():
            continue
        if end_ann_ix is None:
            end_ann_ix = i
            continue
        if token.annotation != spans[end_ann_ix].annotation:
            end_ann_ix = i
            continue
        start_ann_ix = i
        joined_span = to_text(spans[start_ann_ix+1:end_ann_ix])
        if re.fullmatch("[.\s\-,]?[.\s]?", joined_span):
            group = TokenGroup([t.without_annotation(recursive=False) for t in spans[start_ann_ix:end_ann_ix+1]],
                               token.annotation)
            tail = spans[end_ann_ix + 1:] if end_ann_ix < len(spans)-1 else []
            spans = spans[:i] + [group] + tail
        end_ann_ix = start_ann_ix
    return spans


def annotate_text_structured(
    text: str,
    patient_first_names="",
    patient_initials="",
    patient_surname="",
    patient_given_name="",
    names=True,
    locations=True,
    institutions=True,
    dates=True,
    ages=True,
    patient_numbers=True,
    phone_numbers=True,
    urls=True,
    flatten=True,
):
    """
    This method annotates text based on the input that includes names of a patient,
    and a number of flags indicating which PHIs should be annotated
    :param text: The text to be annotated
    :param patient_first_names: First name
    :param patient_initials: Initial
    :param patient_surname: Surname(s)
    :param patient_given_name: Given name
    :param names: Person names, including initials
    :param locations: Geographical locations
    :param institutions: Institutions
    :param dates: Dates
    :param ages: Ages
    :param patient_numbers: Patient numbers
    :param phone_numbers: Phone numbers
    :param urls: Urls and e-mail addresses
    :param flatten: Debug option
    :return:
    """
    annotated_text = annotate_text(
        text,
        patient_first_names=patient_first_names,
        patient_initials=patient_initials,
        patient_surname=patient_surname,
        patient_given_name=patient_given_name,
        names=names,
        locations=locations,
        institutions=institutions,
        dates=dates,
        ages=ages,
        patient_numbers=patient_numbers,
        phone_numbers=phone_numbers,
        urls=urls,
        flatten=flatten,
    )
    if has_nested_tags(annotated_text):
        raise NestedTagsError("Text has nested tags")
    tags = utility.find_tags(annotated_text)
    first_non_whitespace_character_index = utility.get_first_non_whitespace(text)
    # utility.get_annotations does not handle nested tags, so make sure not to pass it text with nested tags
    # Also, utility.get_annotations assumes that all tags are listed in the order they appear in the text
    annotations = utility.get_annotations(annotated_text, tags, first_non_whitespace_character_index)

    # Check if there are any annotations whose start+end do not correspond to the text in the annotation
    mismatched_annotations = [ann for ann in annotations if text[ann.start_ix:ann.end_ix] != ann.text_]
    if len(mismatched_annotations) > 0:
        print('WARNING:', len(mismatched_annotations), 'annotations have texts that do not match the original text')

    return annotations


def has_nested_tags(text):
    open_brackets = 0
    for _, ch in enumerate(text):

        if ch == "<":
            open_brackets += 1

        if ch == ">":
            open_brackets -= 1

        if open_brackets == 2:
            return True

        if open_brackets not in (0, 1):
            raise ValueError("Incorrectly formatted string")

    return False


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

            # Replace this occurence with the appropriate number from dispenser
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
