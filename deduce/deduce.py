"""
Deduce is the main module, from which the annotate and
deidentify_annotations() methods can be imported
"""
import re

from deduce import utility
from nltk.metrics import edit_distance
from .annotate import *
from .utility import flatten_text

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
        flatten=True):

    """
    This method annotates text based on the input that includes names of a patient,
    and a number of flags indicating which PHIs should be annotated
    """

    if not text:
        return text

    # Replace < and > symbols
    text = text.replace("<", "(")
    text = text.replace(">", ")")

    # Deidentify names
    if names:

		# First, based on the rules and lookup lists
        text = annotate_names(text, patient_first_names, patient_initials,
                              patient_surname, patient_given_name)

		# Then, based on the context
        text = annotate_names_context(text)

		# Flatten possible nested tags
        if flatten:
            text = flatten_text(text)

    # Institutions
    if institutions:
        text = annotate_institution(text)


    # Geographical locations
    if locations:
        text = annotate_residence(text)
        text = annotate_address(text)
        text = annotate_postalcode(text)

    # Phone numbers
    if phone_numbers:
        text = annotate_phonenumber(text)

    # Patient numbers
    if patient_numbers:
        text = annotate_patientnumber(text)

    # Dates
    if dates:
        text = annotate_date(text)

	# Ages
    if ages:
        text = annotate_age(text)

    # Urls
    if urls:
        text = annotate_email(text)
        text = annotate_url(text)

    # Merge adjacent tags
    while True:
        oldtext = text
        text = re.sub("<([A-Z]+)\s([^>]+)>[\.\s\-,]?[\.\s]?<\\1\s([^>]+)>", "<\\1 \\2 \\3>", text)
        if text == oldtext:
            break

	# Return text
    return text

def annotate_text_structured(text: str, patient_first_names="", patient_initials="", patient_surname="",
                             patient_given_name="", names=True, locations=True, institutions=True, dates=True,
                             ages=True, patient_numbers=True, phone_numbers=True, urls=True, flatten=True):
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
    annotated_text = annotate_text(text, patient_first_names=patient_first_names, patient_initials=patient_initials,
                                   patient_surname=patient_surname, patient_given_name=patient_given_name, names=names,
                                   locations=locations, institutions=institutions, dates=dates, ages=ages,
                                   patient_numbers=patient_numbers, phone_numbers=phone_numbers, urls=urls,
                                   flatten=flatten)
    tags = utility.find_tags(annotated_text)
    first_non_whitespace_character_index = utility.get_first_non_whitespace(text)
    # utility.get_annotations does not handle nested tags, so make sure not to pass it text with nested tags
    # Also, utility.get_annotations assumes that all tags are listed in the order they appear in the text
    annotations = utility.get_annotations(annotated_text, tags, first_non_whitespace_character_index)
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
    for tagname in ["PERSOON", "LOCATIE", "INSTELLING", "DATUM",
                    "LEEFTIJD", "PATIENTNUMMER", "TELEFOONNUMMER", "URL"]:

        # Find all values that occur within this type of tag
        phi_values = re.findall("<" + tagname + r"\s([^>]+)>", text)
        next_phi_values = []

        # Count unique occurrences (fuzzy) of all values in tags
        dispenser = 1

        # Iterate over all the values in tags
        while  len(phi_values) > 0:

            # Compute which other values have edit distance <=1 (fuzzy matching)
            # compared to this value
            thisval = phi_values[0]
            dist = [edit_distance(x, thisval, transpositions=True) <= 1 for x in phi_values[1:]]

            # Replace this occurence with the appropriate number from dispenser
            text = text.replace("<{} {}>".format(tagname, thisval),
                                "<{}-{}>".format(tagname, dispenser))

            # For all other values
            for index, value in enumerate(dist):

                # If the value matches, replace it as well
                if dist[index]:
                    text = text.replace("<{} {}>".format(tagname, phi_values[index+1]),
                                        "<{}-{}>".format(tagname, str(dispenser)))

                # Otherwise, carry it to the next iteration
                else:
                    next_phi_values.append(phi_values[index+1])

            # This is for the next iteration
            phi_values = next_phi_values
            next_phi_values = []
            dispenser += 1

    # Return text
    return text
