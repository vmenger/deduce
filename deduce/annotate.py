""" The annotate module contains the code for annotating text"""

from nltk.metrics import edit_distance
from .utilcls import Annotation
from .lookup_lists import *
from .tokenizer import join_tokens

from .utility import context
from .utility import is_initial

def insert_annotations(text: str, annotations: list[Annotation]) -> str:
    """
    Inserts the annotations in the list into the text in the appropriate locations
    :param text: the raw text
    :param annotations: the annotations to be inserted
    :return: the text with the inserted annotations
    """
    sorted_annotations = sorted(annotations, key=lambda x: x.start_ix)
    out_text = ""
    last_end_ix = 0
    for annotation in sorted_annotations:
        out_text += (text[last_end_ix:annotation.start_ix] + annotation.to_text())
        last_end_ix = annotation.end_ix
    out_text += text[last_end_ix:]
    return out_text

def remove_annotations_in_range(annotations: list[Annotation], start_ix: int, end_ix: int) -> list[Annotation]:
    """
    Remove all annotations that occur within a given range
    :param annotations: list of annotations
    :param start_ix: starting index where we want to remove
    :param end_ix: ending index where we want to remove
    :return: the annotations excluding those occurring in the range specified
    """
    return [el for el in annotations if el.end_ix <= start_ix or el.start_ix >= end_ix]

def annotate_names(
    text, patient_first_names, patient_initial, patient_surname, patient_given_name
):
    """This function annotates person names, based on several rules."""
    # Tokenize the text
    tokens = tokenize_split(text + " ")
    token_index = -1
    annotations = []

    # Iterate over all tokens
    while token_index < len(tokens) - 1:

        # Current position
        token_index = token_index + 1

        # Current token, and number of tokens already deidentified (used to detect changes)
        token = tokens[token_index]

        # The context of this token
        (_, _, next_token, next_token_index) = context(tokens, token_index)

        ### Prefix based detection
        # Check if the token is a prefix, and the next token starts with a capital
        prefix_condition = (
                token.text.lower() in PREFIXES
                and next_token
                and next_token.text[0].isupper()
                and next_token.text.lower() not in WHITELIST
        )
        # If the condition is met, tag the tokens and continue to the next position
        if prefix_condition:
            start_ix = tokens[token_index].start_ix
            end_ix = tokens[next_token_index].end_ix
            annotations.append(Annotation(start_ix, end_ix, "PREFIXNAAM", text[start_ix:end_ix]))

            token_index = next_token_index
            continue

        ### Interfix based detection
        # Check if the token is an interfix, and the next token is in the list of interfix surnames
        interfix_condition = (
                token.text.lower() in INTERFIXES
                and next_token
                and next_token.text in INTERFIX_SURNAMES
                and next_token.text.lower() not in WHITELIST
        )
        # If condition is met, tag the tokens and continue to the new position
        if interfix_condition:
            start_ix = tokens[token_index].start_ix
            end_ix = tokens[next_token_index].end_ix
            annotations.append(Annotation(start_ix, end_ix, "INTERFIXNAAM", text[start_ix:end_ix]))
            token_index = next_token_index
            continue

        ### First name
        # Check if there is any information in the first_names variable
        if len(patient_first_names) > 1:

            # Because of the extra nested loop over first_names,
            # we can decide if the token has been tagged
            found = False

            # Voornamen
            for patient_first_name in str(patient_first_names).split(" "):

                # Check if the initials match
                if token == patient_first_name[0]:

                    # If followed by a period, also annotate the period
                    if next_token != "" and tokens[token_index + 1][0] == ".":
                        start_ix = tokens[token_index].start_ix
                        end_ix = tokens[token_index+1].end_ix
                        annotations.append(Annotation(start_ix, end_ix, "INITIAALPAT", text[start_ix:end_ix]))
                        if tokens[token_index + 1] == ".":
                            token_index += 1
                        else:
                            tokens[token_index + 1] = tokens[token_index + 1][1:]
                    # Else, annotate the token itself
                    else:
                        start_ix = token.start_ix
                        end_ix = token.end_ix
                        annotations.append(Annotation(start_ix, end_ix, "INITIAALPAT", text[start_ix:end_ix]))

                    # Break the first names loop
                    found = True
                    break

                # Check that either an exact match exists, or a fuzzy match
                # if the token has more than 3 characters
                first_name_condition = token.text == patient_first_name or (
                        len(token.text) > 3
                        and edit_distance(token.text, patient_first_name, transpositions=True)
                        <= 1
                )
                # If the condition is met, tag the token and move on
                if first_name_condition:
                    start_ix = token.start_ix
                    end_ix = token.end_ix
                    annotations.append(Annotation(start_ix, end_ix, "VOORNAAMPAT", text[start_ix:end_ix]))
                    found = True
                    break

            # If a match was found, continue
            if found:
                continue

        ### Initial
        # If the initial is not empty, and the token matches the initial, tag it as an initial
        if len(patient_initial) > 0 and token == patient_initial:
            start_ix = token.start_ix
            end_ix = token.end_ix
            annotations.append(Annotation(start_ix, end_ix, "INITIALENPAT", text[start_ix:end_ix]))
            continue

        ### Surname
        if len(patient_surname) > 1:

            # Surname can consist of multiple tokens, so we will match for that
            surname_pattern = tokenize_split(patient_surname)

            # Iterate over all tokens in the pattern
            my_iter = 0
            counter = 0
            match = False

            # See if there is a fuzzy match, and if there are enough tokens left
            # to match the rest of the pattern
            if edit_distance(token.text, surname_pattern[0].text, transpositions=True) <= 1 and (
                    token_index + len(surname_pattern)
            ) < len(tokens):

                # Found a match
                match = True

                # Iterate over rest of pattern to see if every element matches (fuzzily)
                while counter < len(surname_pattern):
                    # If the distance is too big, disgregard the match

                    if (
                            edit_distance(
                                tokens[token_index + my_iter].text,
                                surname_pattern[my_iter].text,
                                transpositions=True
                            )
                            > 1
                    ):

                        match = False
                        break
                    my_iter += 1
                    counter += 1
            # If a match was found, tag the appropriate tokens, and continue
            if match:
                start_ix = tokens[token_index].start_ix
                end_ix = tokens[token_index+len(surname_pattern)-1].end_ix
                annotations.append(Annotation(start_ix, end_ix, "ACHTERNAAMPAT", text[start_ix:end_ix]))
                token_index = token_index + len(surname_pattern) - 1
                continue

        ### Given name
        # Match if the given name is not empty, and either the token matches exactly
        # or fuzzily when more than 3 characters long
        given_name_condition = len(patient_given_name) > 1 and (
                token.text == patient_given_name
                or (
                        len(token.text) > 3
                        and edit_distance(token, str(patient_given_name), transpositions=True)
                        <= 1
                )
        )
        # If match, tag the token and continue
        if given_name_condition:
            start_ix = token.start_ix
            end_ix = token.end_ix
            annotations.append(Annotation(start_ix, end_ix, "ROEPNAAMPAT", text[start_ix:end_ix]))
            continue

        ### Unknown first and last names
        # For both first and last names, check if the token
        # is on the lookup list and not on the whitelist
        if token.text in FIRST_NAMES and token.text.lower() not in WHITELIST:
            start_ix = token.start_ix
            end_ix = token.end_ix
            annotations.append(Annotation(start_ix, end_ix, "VOORNAAMONBEKEND", text[start_ix:end_ix]))
            continue
        if token.text in SURNAMES and token.text.lower() not in WHITELIST:
            start_ix, end_ix = token.start_ix, token.end_ix
            annotations.append(Annotation(start_ix, end_ix, "ACHTERNAAMONBEKEND", text[start_ix:end_ix]))
            continue
    return annotations

def annotate_names_context(text: str, old_annotations: list[Annotation]) -> list[Annotation]:
    """
    This function annotates person names, based on its context in the text
    :param text: the raw (unannotated) text
    :param old_annotations: the annotations found before looking at the context
    :return: the new list of annotations including those found by context
    """
    # Annotate the text to look for context
    annotated_text = insert_annotations(text, old_annotations)

    # Tokenize text and initiate a list of deidentified tokens
    tokens = tokenize_split(annotated_text + " ")
    new_annotations = []
    token_index = -1
    old_annotations_copy = old_annotations.copy()

    # Iterate over all tokens
    while token_index < len(tokens) - 1:

        # Current token position
        token_index = token_index + 1

        # Current token
        token = tokens[token_index]

        # Context of the token
        (previous_token, previous_token_index, next_token, next_token_index) = context(
            tokens, token_index
        )
        ### Initial or unknown capitalized word, detected by a name or surname that is behind it
        # If the token is an initial, or starts with a capital
        initial_condition = (
                            is_initial(token.text)
                            or (token.text != "" and token.text[0].isupper() and token.text.lower() not in WHITELIST)
                            ) and next_token and (
                                # And the token is followed by either a
                                # found surname, interfix or initial
                                "ACHTERNAAM" in next_token.text or
                                "INTERFIX" in next_token.text or
                                "INITIAAL" in next_token.text
                            )
        # If match, tag the token and continue
        if initial_condition:
            new_annotations.append(Annotation(tokens[token_index].start_ix, tokens[next_token_index].end_ix, "INITIAAL",
                                              text[tokens[token_index].start_ix:tokens[next_token_index].end_ix]))

            token_index = next_token_index
            continue

        ### Interfix preceded by a name, and followed by a capitalized token
        # If the token is an interfix
        interfix_condition = (
                token.text in INTERFIXES
                and
                # And the token is preceded by an initial, found initial or found name
                (
                        is_initial(previous_token.text)
                        or "INITIAAL" in previous_token.text
                        or "NAAM" in previous_token.text
                )
                and
                # And the next token must be capitalized
                next_token.text != ""
                and (next_token.text[0].isupper() or next_token.text[0] == "<")
        )

        # If the condition is met, tag the tokens and continue
        if interfix_condition:
            # Remove some already identified tokens, to prevent double tagging
            start_ix = tokens[previous_token_index].start_ix
            end_ix = tokens[next_token_index].end_ix
            old_annotations_copy = remove_annotations_in_range(old_annotations_copy, start_ix, end_ix)
            new_annotations = remove_annotations_in_range(new_annotations, start_ix, end_ix)
            new_annotations.append(Annotation(start_ix, end_ix, "INTERFIXACHTERNAAM", text[start_ix:end_ix]))
            token_index = next_token_index
            continue

        ### Initial or name, followed by a capitalized word
        # If the token is an initial, or found name or prefix
        initial_name_condition = (
                (
                        is_initial(token.text)
                        or "VOORNAAM" in token.text
                        or "ROEPNAAM" in token.text
                        or "PREFIX" in token.text
                        # And the next token is uppercase and has at least 3 characters
                )
                and len(next_token.text) > 3
                and next_token.text[0].isupper()
                and next_token.text.lower() not in WHITELIST
        )
        # If a match is found, tag and continue
        if initial_name_condition:
            start_ix = tokens[token_index].start_ix
            end_ix = tokens[next_token_index].end_ix
            new_annotations.append(Annotation(start_ix, end_ix, "INITIAALHOOFDLETTERNAAM", text[start_ix:end_ix]))
            token_index = next_token_index
            continue

        ### Patients A and B pattern

        # If the token is "en", and the previous token is tagged, and the next token is capitalized
        and_pattern_condition = (
            token.text == "en"
            and len(previous_token.text) > 0
            and len(next_token.text) > 0
            and "<" in previous_token.text
            and next_token.text[0].isupper()
        )
        # If a match is found, tag and continue
        if and_pattern_condition:
            start_ix = tokens[previous_token_index].start_ix
            end_ix = tokens[next_token_index].end_ix
            old_annotations_copy = remove_annotations_in_range(old_annotations_copy, start_ix, end_ix)
            new_annotations = remove_annotations_in_range(new_annotations, start_ix, end_ix)
            new_annotations.append(Annotation(start_ix, end_ix, "MEERDEREPERSONEN", text[start_ix:end_ix]))
            token_index = next_token_index
            continue

    # If nothing changed, we are done
    if len(new_annotations) == 0 and old_annotations_copy == old_annotations:
        return old_annotations

    # Else, run the annotation based on context again
    else:
        return annotate_names_context(text, Annotation.join_and_sort(old_annotations_copy, new_annotations))

def annotate_residence(text):
    """Annotate residences"""

    # Tokenize text
    tokens = tokenize_split(text)
    tokens_deid = []
    token_index = -1

    # Iterate over tokens
    while token_index < len(tokens) - 1:

        # Current token position and token
        token_index = token_index + 1
        token = tokens[token_index]

        # Find all tokens that are prefixes of the remainder of the text
        prefix_matches = RESIDENCES_TRIE.find_all_prefixes(tokens[token_index:])

        # If none, just append the current token and move to the next
        if len(prefix_matches) == 0:
            tokens_deid.append(token)
            continue

        # Else annotate the longest sequence as residence
        max_list = max(prefix_matches, key=len)
        tokens_deid.append(f"<LOCATIE {join_tokens(max_list)}>")
        token_index += len(max_list) - 1

    # Return the de-identified text
    return join_tokens(tokens_deid)

def replace_altrecht_annotations(text: str, annotations: list) -> list:
    new_annotations = []
    for match in re.finditer('[aA][lL][tT][rR][eE][cC][hH][tT]((\s[A-Z]([\w]*))*)', text):
        start_ix = match.start()
        match_text = match.group(0)
        new_annotations.append(Annotation(start_ix, start_ix + len(match_text), 'INSTELLING', match_text))
    new_annotation_start_ixs = set([ann.start_ix for ann in new_annotations])
    old_annotations_non_overlapping = [ann for ann in annotations if ann.start_ix not in new_annotation_start_ixs]
    return Annotation.join_and_sort(old_annotations_non_overlapping, new_annotations)

def annotate_institution(text: str) -> list:
    """Annotate institutions"""

    # Tokenize, and make a list of non-capitalized tokens (used for matching)
    tokens = tokenize_split(text)
    tokens_lower = [x.text.lower() for x in tokens]
    token_index = -1
    new_annotations = []

    # Iterate over all tokens
    while token_index < len(tokens) - 1:

        # Current token position and token
        token_index = token_index + 1

        # Find all tokens that are prefixes of the remainder of the lowercasetext
        prefix_matches = INSTITUTION_TRIE.find_all_prefixes(tokens_lower[token_index:])

        # If none, just move to the next
        if len(prefix_matches) == 0:
            continue

        # Else annotate the longest sequence as institution
        max_list = max(prefix_matches, key=len)
        joined_institution = join_tokens(tokens[token_index:token_index + len(max_list)])
        annotation = Annotation(joined_institution.start_ix, joined_institution.end_ix, 'INSTELLING',
                                joined_institution.text)
        new_annotations.append(annotation)
        token_index += len(max_list) - 1

    # Detect the word "Altrecht" followed by a capitalized word
    new_annotations = replace_altrecht_annotations(text, new_annotations)

    # Return the text
    return new_annotations

def get_date_replacement_(date_match: re.Match, punctuation_name: str) -> str:
    punctuation = date_match[punctuation_name]
    if len(punctuation) != 1:
        punctuation = ' '
    return '<DATUM ' + date_match.group(1) + '>' + punctuation

### Other annotation is done using a selection of finely crafted
### (but alas less finely documented) regular expressions.
def annotate_date(text):
    # Name the punctuation mark that comes after a date, for replacement purposes
    punctuation_name = 'n'
    text = re.sub("(([1-9]|0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012]|[1-9])([- /.]{,2}(\d{4}|\d{2}))?)(?P<" +
                  punctuation_name + ">\D)(?![^<]*>)",
                  lambda date_match: get_date_replacement_(date_match, punctuation_name),
                  text)
    text = re.sub(
        "(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)" +
        "([- /.]{,2}(\d{4}|\d{2}))?)(?P<" + punctuation_name + ">\D)(?![^<]*>)",
        lambda date_match: get_date_replacement_(date_match, punctuation_name),
        text)
    return text


def annotate_age(text):
    """Annotate ages"""
    text = re.sub(
        "(\d{1,3})([ -](jarige|jarig|jaar))(?![^<]*>)", "<LEEFTIJD \\1>\\2", text
    )
    return text


def annotate_phonenumber(text):
    """Annotate phone numbers"""
    text = re.sub(
        "(((0)[1-9]{2}[0-9][-]?[1-9][0-9]{5})|((\\+31|0|0031)[1-9][0-9][-]?[1-9][0-9]{6}))(?![^<]*>)",
        "<TELEFOONNUMMER \\1>",
        text,
    )

    text = re.sub(
        "(((\+31|0|0031)6)[-]?[1-9][0-9]{7})(?![^<]*>)",
        "<TELEFOONNUMMER \\1>",
        text,
    )

    text = re.sub(
        "((\(\d{3}\)|\d{3})\s?\d{3}\s?\d{2}\s?\d{2})(?![^<]*>)",
        "<TELEFOONNUMMER \\1>",
        text,
    )

    return text


def annotate_patientnumber(text):
    """Annotate patient numbers"""
    text = re.sub("(\d{7})(?![^<]*>)", "<PATIENTNUMMER \\1>", text)
    return text


def annotate_postalcode(text):
    """Annotate postal codes"""
    text = re.sub(
        "(((\d{4} [A-Z]{2})|(\d{4}[a-zA-Z]{2})))(?P<n>\W)(?![^<]*>)",
        "<LOCATIE \\1>\\5",
        text,
    )
    text = re.sub("<LOCATIE\s(\d{4}mg)>", "\\1", text)
    text = re.sub("([Pp]ostbus\s\d{5})", "<LOCATIE \\1>", text)
    return text


def get_address_match_replacement(match: re.Match) -> str:
    text = match.group(0)
    stripped = text.strip()
    if len(text) == len(stripped):
        return f"<LOCATIE {text}>"

    return f"<LOCATIE {stripped}>{' ' * (len(text) - len(stripped))}"


def annotate_address(text):
    """Annotate addresses"""
    text = re.sub(
        r"([A-Z]\w+(straat|laan|hof|plein|gracht|weg|steeg|pad|dijk|baan|dam|dreef|"
        r"kade|markt|park|plantsoen|singel|bolwerk)[\s\n\r]((\d+){1,6}(\w{0,2})?|(\d+){0,6}))",
        get_address_match_replacement,
        text,
    )
    return text


def annotate_email(text):
    """Annotate emails"""
    text = re.sub(
        "(([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?))(?![^<]*>)",
        "<URL \\1>",
        text,
    )

    return text


def annotate_url(text):
    """Annotate urls"""
    text = re.sub(
        "((?!mailto:)(?:http|https|ftp)://(?:\\S+(?::\\S*)?@)?(?:(?:(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])" +
        "(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}\.(?:[0-9]\d?|1\d\d|2[0-4]\d|25[0-4])" +
        "|(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+(?:\\.(?:[a-z\\u00a1-\\uffff0-9]+-?)" +
        "*[a-z\\u00a1-\\uffff0-9]+)*\.[a-z¡-￿]{2,})|localhost)(?::\\d{2,5})?(?:([/?#])" +
        "[^\\s]*)?)(?![^<]*>)",
        "<URL \\1>",
        text,
    )

    text = re.sub(
        "([\w\d.-]{3,}(\.)(nl|com|net|be)(/[^\s]+)?)(?![^<]*>)", "<URL \\1>", text
    )

    return text
