""" The annotate module contains the code for annotating text"""

from nltk.metrics import edit_distance

from .lookup_lists import *
from .tokenizer import join_tokens
from .utilcls import Token, TokenGroup, AbstractSpan
from .utility import context
from .utility import is_initial


def annotate_names(
    tokens: list[Token], patient_first_names, patient_initial, patient_surname, patient_given_name
) -> list[Token]:
    """This function annotates person names, based on several rules."""

    # Tokenize the text
    tokens_deid = []
    token_index = -1

    # Iterate over all tokens
    while token_index < len(tokens) - 1:

        # Current position
        token_index = token_index + 1

        # Current token, and number of tokens already deidentified (used to detect changes)
        token = tokens[token_index]
        num_tokens_deid = len(tokens_deid)

        # The context of this token
        (_, _, next_token, next_token_index) = context(tokens, token_index)

        ### Prefix based detection
        # Check if the token is a prefix, and the next token starts with a capital
        prefix_condition = (
            not token.is_annotation() and token.text.lower() in PREFIXES
            and next_token is not None and next_token.text != ''
            and next_token.text[0].isupper()
            and next_token.text.lower() not in WHITELIST
        )

        # If the condition is met, tag the tokens and continue to the next position
        if prefix_condition:
            tokens_deid.append(TokenGroup(tokens[token_index:next_token_index+1], 'PREFIXNAAM'))
            token_index = next_token_index
            continue

        ### Interfix based detection
        # Check if the token is an interfix, and the next token is in the list of interfix surnames
        interfix_condition = (
            not token.is_annotation() and token.text.lower() in INTERFIXES
            and next_token is not None and next_token.text != ''
            and not next_token.is_annotation() and next_token.text in INTERFIX_SURNAMES
            and next_token.text.lower() not in WHITELIST
        )

        # If condition is met, tag the tokens and continue to the new position
        if interfix_condition:
            tokens_deid.append(TokenGroup(tokens[token_index: next_token_index + 1], 'INTERFIXNAAM'))
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
                if not token.is_annotation() and token.text == patient_first_name[0]:

                    # If followed by a period, also annotate the period
                    if next_token is not None and next_token.text != "" \
                            and not tokens[token_index + 1].is_annotation() and tokens[token_index + 1].text[0] == ".":
                        tokens_deid.append(TokenGroup(
                            [tokens[token_index],
                             Token(tokens[token_index].end_ix, tokens[token_index].end_ix + 1, '.', '')],
                            'INITIAALPAT'))
                        if not tokens[token_index + 1].is_annotation() and tokens[token_index + 1].text == ".":
                            token_index += 1
                        else:
                            tokens[token_index + 1] = tokens[token_index + 1].subset(start_ix=1)

                    # Else, annotate the token itself
                    else:
                        tokens_deid.append(TokenGroup([token], 'INITIAALPAT'))

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
                    tokens_deid.append(TokenGroup([token], 'VOORNAAMPAT'))
                    found = True
                    break

            # If a match was found, continue
            if found:
                continue

        ### Initial
        # If the initial is not empty, and the token matches the initial, tag it as an initial
        if len(patient_initial) > 0 and not token.is_annotation() and token.text == patient_initial:
            tokens_deid.append(TokenGroup([token], 'INITIALENPAT'))
            continue

        ### Surname
        if len(patient_surname) > 1:

            # Surname can consist of multiple tokens, so we will match for that
            surname_pattern = tokenize_split(patient_surname)

            # Iterate over all tokens in the pattern
            counter = 0
            match = False

            # See if there is a fuzzy match, and if there are enough tokens left
            # to match the rest of the pattern
            if not token.is_annotation() and edit_distance(token.text, surname_pattern[0], transpositions=True) <= 1 \
                    and (
                token_index + len(surname_pattern)
            ) < len(tokens):

                # Found a match
                match = True

                # Iterate over rest of pattern to see if every element matches (fuzzily)
                while counter < len(surname_pattern):

                    # If the distance is too big, disgregard the match
                    if (
                        not tokens[token_index + counter].is_annotation()
                        and edit_distance(
                            tokens[token_index + counter].text,
                            surname_pattern[counter],
                            transpositions=True,
                        )
                        > 1
                    ):

                        match = False
                        break

                    counter += 1

            # If a match was found, tag the appropriate tokens, and continue
            if match:
                group = TokenGroup(tokens[token_index: token_index + len(surname_pattern)], 'ACHTERNAAMPAT')
                tokens_deid.append(group)
                token_index = token_index + len(surname_pattern) - 1
                continue

        ### Given name
        # Match if the given name is not empty, and either the token matches exactly
        # or fuzzily when more than 3 characters long
        given_name_condition = len(patient_given_name) > 1 and (
            not token.is_annotation() and
            token.text == patient_given_name
            or (
                not token.is_annotation()
                and len(token.text) > 3
                and edit_distance(token.text, str(patient_given_name), transpositions=True)
                <= 1
            )
        )

        # If match, tag the token and continue
        if given_name_condition:
            tokens_deid.append(TokenGroup([token], 'ROEPNAAMPAT'))
            continue

        ### Unknown first and last names
        # For both first and last names, check if the token
        # is on the lookup list and not on the whitelist
        if not token.is_annotation() and token.text in FIRST_NAMES and token.text.lower() not in WHITELIST:
            tokens_deid.append(TokenGroup([token], 'VOORNAAMONBEKEND'))
            continue

        if not token.is_annotation() and token.text in SURNAMES and token.text.lower() not in WHITELIST:
            tokens_deid.append(TokenGroup([token], 'ACHTERNAAMONBEKEND'))
            continue

        ### Wrap up
        # Nothing has been added (ie no deidentification tag) to tokens_deid,
        # so we can safely add the token itself
        if len(tokens_deid) == num_tokens_deid:
            tokens_deid.append(token)

    # Return the deidentified tokens as a piece of text
    return tokens_deid


def annotate_names_context(tokens: list[Token]) -> list[Token]:
    """This function annotates person names, based on its context in the text"""

    # Tokenize text and initiate a list of deidentified tokens
    tokens_deid = []
    token_index = -1

    # Iterate over all tokens
    while token_index < len(tokens) - 1:

        # Current token position
        token_index = token_index + 1

        # Current token
        token = tokens[token_index]

        # Number of tokens, used to detect change
        numtokens_deid = len(tokens_deid)

        # Context of the token
        (previous_token, previous_token_index, next_token, next_token_index) = context(
            tokens, token_index
        )

        ### Initial or unknown capitalized word, detected by a name or surname that is behind it
        # If the token is an initial, or starts with a capital
        initial_condition = (
            is_initial(token)
            or (not token.is_annotation() and token.text != '' and token.text[0].isupper()
                and token.text.lower() not in WHITELIST)
        ) and (
            # And the token is followed by either a
            # found surname, interfix or initial
            next_token is not None
            and next_token.is_annotation()
            and any([tag in next_token.get_full_annotation() for tag in ('ACHTERNAAM', 'INTERFIX', 'INITIAAL')])
        )

        # If match, tag the token and continue
        if initial_condition:
            tokens_deid.append(TokenGroup(tokens[token_index: next_token_index + 1], 'INITIAAL'))
            token_index = next_token_index
            continue

        ### Interfix preceded by a name, and followed by a capitalized token

        # If the token is an interfix
        interfix_condition = (
            not token.is_annotation()
            and token.text in INTERFIXES
            and
            # And the token is preceded by an initial, found initial or found name
            (
                is_initial(previous_token)
                or (
                        previous_token.is_annotation()
                        and any([tag in previous_token.get_full_annotation() for tag in ('INITIAAL', 'NAAM')])
                )
            )
            and
            # And the next token must be capitalized
            next_token is not None and next_token.text != ''
            and (next_token.text[0].isupper() or next_token.is_annotation())
        )

        # If the condition is met, tag the tokens and continue
        if interfix_condition:
            # Remove some already identified tokens, to prevent double tagging
            (_, previous_token_index_deid, _, _) = context(
                tokens_deid, len(tokens_deid)
            )
            deid_tokens_to_keep = tokens_deid[previous_token_index_deid:]
            tokens_deid = tokens_deid[:previous_token_index_deid]
            group = TokenGroup(deid_tokens_to_keep + tokens[token_index:next_token_index + 1], 'INTERFIXACHTERNAAM')
            tokens_deid.append(group)
            token_index = next_token_index
            continue

        ### Initial or name, followed by a capitalized word
        # If the token is an initial, or found name or prefix
        initial_name_condition = (
            (
                is_initial(token)
                or (
                        token.is_annotation()
                        and any([tag in token.get_full_annotation() for tag in ('VOORNAAM', 'ROEPNAAM', 'PREFIX')])
                )
                # And the next token is uppercase and has at least 3 characters
            )
            and next_token is not None and len(next_token.text) > 3
            and not next_token.is_annotation() and next_token.text[0].isupper()
            and next_token.text.lower() not in WHITELIST
        )

        # If a match is found, tag and continue
        if initial_name_condition:
            tokens_deid.append(TokenGroup(tokens[token_index: next_token_index + 1], 'INITIAALHOOFDLETTERNAAM'))
            token_index = next_token_index
            continue

        ### Patients A and B pattern

        # If the token is "en", and the previous token is tagged, and the next token is capitalized
        and_pattern_condition = (
            not token.is_annotation() and token.text == 'en'
            and previous_token is not None and len(previous_token.text) > 0
            and next_token is not None and len(next_token.text) > 0
            and previous_token.is_annotation()
            and not next_token.is_annotation() and next_token.text[0].isupper()
        )

        # If a match is found, tag and continue
        if and_pattern_condition:
            (previous_token_deid, previous_token_index_deid, _, _) = context(
                tokens_deid, len(tokens_deid)
            )
            tokens_deid = tokens_deid[:previous_token_index_deid]
            token_group = TokenGroup([previous_token_deid] + tokens[previous_token_index + 1: next_token_index + 1],
                                     'MEERDEREPERSONEN')
            tokens_deid.append(token_group)
            token_index = next_token_index
            continue

        # Nothing has been added (ie no deidentification tag) to tokens_deid,
        # so we can safely add the token itself
        if len(tokens_deid) == numtokens_deid:
            tokens_deid.append(token)

    # If nothing changed, we are done
    if tokens == tokens_deid:
        return tokens

    # Else, run the annotation based on context again
    return annotate_names_context(tokens_deid)


def annotate_residence(spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """Annotate residences"""

    # Tokenize text
    tokens_deid = []
    token_index = -1

    # Iterate over tokens
    while token_index < len(spans) - 1:

        # Current token position and token
        token_index = token_index + 1
        token = spans[token_index]

        # If this is an annotation, it cannot also be a residence
        if token.is_annotation():
            tokens_deid.append(token)
            continue

        # Find all tokens that are prefixes of the remainder of the text
        prefix_matches = RESIDENCES_TRIE.find_all_prefixes([s.as_text() for s in spans[token_index:]])

        # If none, just append the current token and move to the next
        if len(prefix_matches) == 0:
            tokens_deid.append(token)
            continue

        # Else annotate the longest sequence as residence
        max_list = max(prefix_matches, key=len)
        tokens_deid.append(TokenGroup(tokens_deid[token_index:token_index + len(max_list)], 'LOCATIE'))
        token_index += len(max_list) - 1

    # Return the de-identified text
    return tokens_deid

def annotate_institution(annotated_spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """Annotate institutions"""

    # Tokenize, and make a list of non-capitalized tokens (used for matching)
    tokens_lower = [x.text.lower() for x in annotated_spans]
    tokens_deid = []
    token_index = -1

    # Iterate over all tokens
    while token_index < len(annotated_spans) - 1:

        # Current token position and token
        token_index = token_index + 1
        token = annotated_spans[token_index]

        # Find all tokens that are prefixes of the remainder of the lowercase text
        prefix_matches = INSTITUTION_TRIE.find_all_prefixes(tokens_lower[token_index:])

        # If none, just append the current token and move to the next
        if len(prefix_matches) == 0:
            tokens_deid.append(token)
            continue

        # Else annotate the longest sequence as institution
        max_list = max(prefix_matches, key=len)
        joined_institution = TokenGroup(annotated_spans[token_index:token_index + len(max_list)], 'INSTELLING')
        tokens_deid.append(joined_institution)
        token_index += len(max_list) - 1

    # Detect the word "Altrecht" followed by a capitalized word
    ix = 0
    final_spans = []
    while ix < len(tokens_deid):
        annotated_span = tokens_deid[ix]
        # See if this is an annotation with type INSTELLING and lowercased text altrecht
        if not annotated_span.is_annotation() \
                or annotated_span.get_full_annotation() != 'INSTELLING' \
                or annotated_span.text.lower() != 'altrecht':
            final_spans.append(annotated_span)
            ix += 1
            continue
        # Now look for iterations of the pattern (space, capital)
        jx = ix
        while jx < len(tokens_deid) - 2:
            space = tokens_deid[jx+1]
            capital = tokens_deid[jx+2]
            if space.is_annotation() or not re.fullmatch('\s', space.text):
                break
            if capital.is_annotation() or not capital.text[0].isupper():
                break
            jx += 2
        if jx == ix:
            final_spans.append(annotated_span)
            ix += 1
            continue
        stripped_altrecht = Token(annotated_span.start_ix, annotated_span.end_ix, annotated_span.text, '')
        # noinspection PyTypeChecker
        altrecht_with_capitals = [stripped_altrecht] + tokens_deid[ix+1:jx+1]
        final_spans.append(TokenGroup(altrecht_with_capitals, 'INSTELLING'))
        ix = jx + 1

    # Return the text
    return final_spans

def get_date_replacement_(date_match: re.Match, punctuation_name: str) -> str:
    punctuation = date_match[punctuation_name]
    if len(punctuation) != 1:
        punctuation = ' '
    return '<DATUM ' + date_match.group(1) + '>' + punctuation

### Other annotation is done using a selection of finely crafted
### (but alas less finely documented) regular expressions.
def annotate_date(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    patterns = [r"(([1-9]|0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012]|[1-9])([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)"
                r"(?![^<]*>)",
                r"(\d{1,2}[^\w]{,2}"
                r"(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)"
                r"([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)(?![^<]*>)"]
    for pattern in patterns:
        matches = [strip_match_and_tag_(match.group(1), match.start(1), 'DATUM')
                   for match in re.finditer(pattern, text)]
        spans = insert_matches_(matches, spans)
    return spans

def annotate_age(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    matches = [strip_match_and_tag_(match.group(1), match.start(1), 'LEEFTIJD')
               for match in re.finditer("(\d{1,3})([ -](jarige|jarig|jaar))(?![^<]*>)", text)]
    return insert_matches_(matches, spans)


def annotate_phone_number(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """Annotate phone numbers"""
    patterns = ["(((0)[1-9]{2}[0-9][-]?[1-9][0-9]{5})|((\\+31|0|0031)[1-9][0-9][-]?[1-9][0-9]{6}))(?![^<]*>)",
                "(((\\+31|0|0031)6){1}[-]?[1-9]{1}[0-9]{7})(?![^<]*>)",
                "((\(\d{3}\)|\d{3})\s?\d{3}\s?\d{2}\s?\d{2})(?![^<]*>)"]
    for pattern in patterns:
        matches = [strip_match_and_tag_(match.group(1), match.start(1), 'TELEFOONNUMMER')
                   for match in re.finditer(pattern, text)]
        spans = insert_matches_(matches, spans)
    return spans


def annotate_patient_number(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """Annotate patient numbers"""
    return insert_matches_(
        [strip_match_and_tag_(match.group(1), match.start(1), 'PATIENTNUMMER')
         for match in re.finditer("(\d{7})(?![^<]*>)", text)],
        spans
    )

def remove_mg_(spans: list[AbstractSpan]) -> list[AbstractSpan]:
    return [span.without_annotation()
            if span.is_annotation() and span.annotation == 'LOCATIE' and re.fullmatch('(\d{4}mg)', span.text)
            else span
            for span in spans]

def parse_postal_code_(match: re.Match) -> Token:
    return Token(match.start(1), match.end(1), match.group(1), 'LOCATIE')


def annotate_postcode(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """
    Annotate postal codes
    :param text: the entire text to look in
    :param spans: a list of previously found spans that cover the entire text
    :return: a list of spans covering the entire text including the new annotations
    """
    # Annotate everything that looks like a postcode
    pattern = "(((\d{4} [A-Z]{2})|(\d{4}[a-zA-Z]{2})))(?P<n>\W)(?![^<]*>)"
    post_box_matches = [parse_postal_code_(match) for match in re.finditer(pattern, text)]
    new_spans = insert_matches_(post_box_matches, spans)

    # Remove "postcodes" that are really milligrams
    new_spans = remove_mg_(new_spans)

    # Annotate post boxes
    post_box_matches = [Token(match.start(0), match.end(0), match.group(0), 'LOCATIE')
                        for match in re.finditer("([Pp]ostbus\s\d{5})", text)]
    new_spans = insert_matches_(post_box_matches, new_spans)

    return new_spans
    """Annotate postal codes"""
    """text = re.sub(
        ,
        "<LOCATIE \\1>\\5",
        text,
    )
    text = re.sub("<LOCATIE\s(\d{4}mg)>", "\\1", text)
    text = re.sub(, "<LOCATIE \\1>", text)
    return text"""

def intersect_(span: AbstractSpan, match_token: AbstractSpan) -> bool:
    return match_token.start_ix < span.end_ix and match_token.end_ix > span.start_ix

def strip_match_and_tag_(text: str, start_ix: int, annotation: str) -> AbstractSpan:
    stripped = text.strip()
    new_start_ix = text.index(stripped[0]) + start_ix
    return Token(new_start_ix, new_start_ix + len(stripped), stripped, annotation)

def split_at_match_boundaries_(
        spans: list[AbstractSpan],
        match_token: AbstractSpan
) -> list[TokenGroup]:
    assert spans, 'The match does not correspond to the spans'
    assert not any([span.is_annotation() for span in spans]), \
        'The spans corresponding to the match belong to annotations'
    assert match_token.is_annotation(), 'The matched token is not annotated'
    if len(spans) == 1:
        return [spans[0].subset(start_ix=match_token.start_ix, end_ix=match_token.end_ix).with_annotation(match_token.annotation)]
    split_spans = []
    component_spans = []
    if match_token.start_ix > spans[0].start_ix:
        split_spans.append(spans[0].subset(end_ix=match_token.start_ix))
        component_spans.append(spans[0].subset(start_ix=match_token.start_ix))
    else:
        component_spans.append(spans[0])
    if len(spans) >= 3:
        component_spans += spans[1:len(spans)-1]
    if match_token.end_ix < spans[-1].end_ix:
        component_spans.append(spans[-1].subset(end_ix=match_token.end_ix))
        last_span = spans[-1].subset(start_ix=match_token.end_ix)
    else:
        component_spans.append(spans[-1])
        last_span = None
    split_spans.append(TokenGroup(component_spans, match_token.annotation))
    if last_span:
        split_spans.append(last_span)
    return split_spans

def insert_match_(match: AbstractSpan, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """
    Given a match in the text corresponding to an address, and the entire list of spans in the text,
    update the list of spans to include the new annotation
    :param match: a regular expression match
    :param spans: the list of previously computed spans
    :return: the new list of spans, including the newly found annotation
    """
    span_ixs = [ix for ix, span in enumerate(spans) if intersect_(span, match)]
    if span_ixs != list(range(span_ixs[0], len(span_ixs) + span_ixs[0])):
        raise ValueError('The match corresponds to non-consecutive spans')
    new_spans = split_at_match_boundaries_([spans[ix] for ix in span_ixs], match)
    return spans[:span_ixs[0]] + new_spans + spans[span_ixs[-1]+1:]

def insert_matches_(matches: list[AbstractSpan], spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """
    Create annotations for the patterns found
    :param matches: the matches found in the text
    :param spans: a list of previously found spans that cover the entire text
    :return: a new list of spans covering the entire text, with the new annotations embedded in them
    """
    new_spans = spans.copy()
    for match in matches:
        new_spans = insert_match_(match, new_spans)
    return new_spans

def annotate_address(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """
    Annotate addresses. This is much easier if we use the original text, so we take two inputs
    :param text: The original text
    :param spans: The spans previously computed for this text
    :return: a new list of spans, potentially with address annotations
    """
    pattern = r"([A-Z]\w+(straat|laan|hof|plein|gracht|weg|pad|dijk|baan|dam|dreef|kade|markt|park|plantsoen|singel|bolwerk)[\s\n\r]((\d+){1,6}(\w{0,2})?|(\d+){0,6}))"
    matches = [strip_match_and_tag_(match.group(0), match.start(0), 'LOCATIE') for match in re.finditer(pattern, text)]
    return insert_matches_(matches, spans)


def annotate_email(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """Annotate emails"""
    pattern = "(([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?))(?![^<]*>)"
    matches = [strip_match_and_tag_(match.group(1), match.start(1), 'URL') for match in re.finditer(pattern, text)]
    return insert_matches_(matches, spans)


def annotate_url(text: str, spans: list[AbstractSpan]) -> list[AbstractSpan]:
    """Annotate urls"""
    patterns = [r"((?!mailto:)(?:(?:http|https|ftp)://)(?:\\S+(?::\\S*)?@)?(?:(?:(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])"
                r"(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}(?:\\.(?:[0-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))|"
                r"(?:(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)(?:\\.(?:[a-z\\u00a1-\\uffff0-9]+-?)"
                r"*[a-z\\u00a1-\\uffff0-9]+)*(?:\\.(?:[a-z\\u00a1-\\uffff]{2,})))|localhost)(?::\\d{2,5})?"
                r"(?:(/|\\?|#)[^\\s]*)?)(?![^<]*>)",
                r"([\w\d\.-]{3,}(\.)(nl|com|net|be)(/[^\s]+){,1})(?![^<]*>)"]
    for pattern in patterns:
        matches = [strip_match_and_tag_(match.group(1), match.start(1), 'URL') for match in re.finditer(pattern, text)]
        spans = insert_matches_(matches, spans)
    return spans
