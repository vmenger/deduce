""" The annotate module contains the code for annotating text"""
import re

from nltk.metrics import edit_distance

from .tokenizer import tokenize_split
from .tokenizer import join_tokens

from .utility import context
from .utility import is_initial

from .lookup_lists import *


def annotate_names(text, patient_first_names, patient_initial, patient_surname, patient_given_name):
    """ This function annotates person names, based on several rules. """

    # Tokenize the text
    tokens = tokenize_split(text + " ")
    tokens_deid = []
    token_index = -1

    # Iterate over all tokens
    while token_index < len(tokens)-1:

        # Current position
        token_index = token_index+1

        # Current token, and number of tokens already deidentified (used to detect changes)
        token = tokens[token_index]
        numtokens_deid = len(tokens_deid)

        # The context of this token
        (previous_token, previous_token_index,
         next_token, next_token_index) = context(tokens, token_index)

        ### Prefix based detection
        # Check if the token is a prefix, and the next token starts with a capital
        prefix_condition = (token.lower() in PREFIXES and
                            next_token != "" and
                            next_token[0].isupper() and
                            next_token.lower() not in WHITELIST
                           )

        # If the condition is met, tag the tokens and continue to the next position
        if prefix_condition:
            tokens_deid.append(
                "<PREFIXNAAM {}>".format(join_tokens(tokens[token_index:next_token_index+1]))
                )
            token_index = next_token_index
            continue

        ### Interfix based detection
        # Check if the token is an interfix, and the next token is in the list of interfix surnames
        interfix_condition = (token.lower() in INTERFIXES and
                              next_token != "" and
                              next_token in INTERFIX_SURNAMES and
                              next_token.lower() not in WHITELIST
                             )

        # If condition is met, tag the tokens and continue to the new position
        if interfix_condition:
            tokens_deid.append(
                "<INTERFIXNAAM {}>".format(join_tokens(tokens[token_index:next_token_index+1]))
                )
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
                    if next_token != "" and tokens[token_index+1][0] == ".":
                        tokens_deid.append(
                            "<INITIAALPAT {}> ".format(
                                join_tokens(tokens[token_index:token_index+2])
                                )
                            )
                        token_index += 1

                    # Else, annotate the token itself
                    else:
                        tokens_deid.append("<INITIAALPAT {}>".format(token))

                    # Break the first names loop
                    found = True
                    break

                # Check that either an exact match exists, or a fuzzy match
                # if the token has more than 3 characters
                first_name_condition = (token == patient_first_name or
                                        (len(token) > 3 and
                                         edit_distance(token,
                                                       patient_first_name,
                                                       transpositions=True) <= 1
                                        )
                                       )

                # If the condition is met, tag the token and move on
                if first_name_condition:
                    tokens_deid.append("<VOORNAAMPAT {}>".format(token))
                    found = True
                    break

            # If a match was found, continue
            if found:
                continue

        ### Initial
        # If the initial is not empty, and the token matches the initial, tag it as an initial
        if len(patient_initial) > 0 and token == patient_initial:
            tokens_deid.append("<INITIALENPAT {}>".format(token))
            continue

        ### Surname
        if len(patient_surname) > 1:

            # Surname can consist of multiple tokens, so we will match for that
            surname_pattern = tokenize_split(patient_surname)

            # Iterate over all tokens in the pattern
            iter = 0
            match = False

            # See if there is a fuzzy match, and if there are enough tokens left
            # to match the rest of the pattern
            if(edit_distance(token, surname_pattern[0], transpositions=True) <= 1 and
               (token_index + len(surname_pattern)) < len(tokens)
              ):

                # Found a match
                match = True

                # Iterate over rest of pattern to see if every element matches (fuzzily)
                while iter < len(surname_pattern):

                    # If the distance is too big, disgregard the match
                    if edit_distance(tokens[token_index + iter],
                                     surname_pattern[iter],
                                     transpositions=True) > 1:

                        match = False
                        break

                    iter += 1

            # If a match was found, tag the appropriate tokens, and continue
            if match:
                tokens_deid.append(
                    "<ACHTERNAAMPAT {}>".format(
                        join_tokens(tokens[token_index:token_index+len(surname_pattern)])
                        )
                    )
                token_index = token_index+len(surname_pattern)-1
                continue

        ### Given name
        # Match if the given name is not empty, and either the token matches exactly
        # or fuzzily when more than 3 characters long
        given_name_condition = (len(patient_given_name) > 1 and
                                (token == patient_given_name or
                                 (len(token) > 3 and
                                  edit_distance(token,
                                                str(patient_given_name),
                                                transpositions=True) <= 1
                                 )
                                )
                               )

        # If match, tag the token and continue
        if given_name_condition:
            tokens_deid.append("<ROEPNAAMPAT {}>".format(token))
            continue

        ### Unknown first and last names
        # For both first and last names, check if the token
        # is on the lookup list and not on the whitelist
        if token in FIRST_NAMES and token.lower() not in WHITELIST:
            tokens_deid.append("<VOORNAAMONBEKEND {}>".format(token))
            continue

        if token in SURNAMES and token.lower() not in WHITELIST:
            tokens_deid.append("<ACHTERNAAMONBEKEND {}>".format(token))
            continue

        ### Wrap up
        # Nothing has been added (ie no deidentification tag) to tokens_deid,
        # so we can safely add the token itself
        if len(tokens_deid) == numtokens_deid:
            tokens_deid.append(token)

    # Return the deidentified tokens as a piece of text
    return join_tokens(tokens_deid).strip()

def annotate_names_context(text):
    """ This function annotates person names, based on its context in the text """

    # Tokenize text and initiate a list of deidentified tokens
    tokens = tokenize_split(text + " ")
    tokens_deid = []
    token_index = -1

    # Iterate over all tokens
    while token_index < len(tokens)-1:

        # Current token position
        token_index = token_index+1

        # Current token
        token = tokens[token_index]

        # Number of tokens, used to detect change
        numtokens_deid = len(tokens_deid)

        # Context of the token
        (previous_token, previous_token_index,
         next_token, next_token_index) = context(tokens, token_index)

        ### Initial or unknown capitalized word, detected by a name or surname that is behind it
                            # If the token is an initial, or starts with a capital
        initial_condition = (is_initial(token) or
                             (token != "" and
                              token[0].isupper() and
                              token.lower() not in WHITELIST
                             )
                            ) and (
                                # And the token is followed by either a
                                # found surname, interfix or initial
                                "ACHTERNAAM" in next_token or
                                "INTERFIX" in next_token or
                                "INITIAAL" in next_token
                            )

        # If match, tag the token and continue
        if initial_condition:
            tokens_deid.append(
                "<INITIAAL {}>".format(join_tokens(tokens[token_index:next_token_index+1]))
                )
            token_index = next_token_index
            continue

        ### Interfix preceded by a name, and followed by a capitalized token

                              # If the token is an interfix
        interfix_condition = (token in INTERFIXES and
                              # And the token is preceded by an initial, found initial or found name
                              (is_initial(previous_token) or
                               "INITIAAL" in previous_token or
                               "NAAM" in previous_token
                              ) and
                              # And the next token must be capitalized
                              next_token != "" and
                              (next_token[0].isupper() or
                               next_token[0] == "<"
                              )
                             )


        # If the condition is met, tag the tokens and continue
        if interfix_condition:
            # Remove some already identified tokens, to prevent double tagging
            (_, previous_token_index_deid, _, _) = context(tokens_deid, len(tokens_deid))
            tokens_deid = tokens_deid[:previous_token_index_deid]
            tokens_deid.append(
                "<INTERFIXACHTERNAAM {}>".format(
                    join_tokens(tokens[previous_token_index : next_token_index+1])
                    )
                )
            token_index = next_token_index
            continue

        ### Initial or name, followed by a capitalized word
                                 # If the token is an initial, or found name or prefix
        initial_name_condition = ((is_initial(token) or
                                   "VOORNAAM" in token or
                                   "ROEPNAAM" in token or
                                   "PREFIX" in token
                                   # And the next token is uppercase and has at least 3 characters
                                  ) and
                                  len(next_token) > 3 and
                                  next_token[0].isupper() and
                                  next_token.lower() not in WHITELIST
                                 )

        # If a match is found, tag and continue
        if initial_name_condition:
            tokens_deid.append(
                "<INITIAALHOOFDLETTERNAAM {}>".format(
                    join_tokens(tokens[token_index:next_token_index+1])
                    )
                )
            token_index = next_token_index
            continue

        ### Patients A and B pattern

        # If the token is "en", and the previous token is tagged, and the next token is capitalized
        and_pattern_condition = (token == "en" and
                                 len(previous_token) > 0 and
                                 len(next_token) > 0 and
                                 "<" in previous_token and
                                 next_token[0].isupper()
                                )

        # If a match is found, tag and continue
        if and_pattern_condition:
            (_, previous_token_index_deid, _, _) = context(tokens_deid, len(tokens_deid))
            tokens_deid = tokens_deid[:previous_token_index_deid]
            tokens_deid.append(
                "<MEERDEREPERSONEN {}>".format(
                    join_tokens(tokens[previous_token_index:next_token_index+1])
                    )
                )
            token_index = next_token_index
            continue

        # Nothing has been added (ie no deidentification tag) to tokens_deid,
        # so we can safely add the token itself
        if len(tokens_deid) == numtokens_deid:
            tokens_deid.append(token)

    # Join the tokens again to form the de-identified text
    textdeid = join_tokens(tokens_deid).strip()

    # If nothing changed, we are done
    if text == textdeid:
        return textdeid

    # Else, run the annotation based on context again
    else:
        return annotate_names_context(textdeid)

def annotate_residence(text):
    """ Annotate residences """

    # Tokenize text
    tokens = tokenize_split(text)
    tokens_deid = []
    token_index = -1

    # Iterate over tokens
    while token_index < len(tokens)-1:

        # Current token position and token
        token_index = token_index+1
        token = tokens[token_index]

        # Find all tokens that are prefixes of the remainder of the text
        prefix_matches = RESIDENCES_TRIE.find_all_prefixes(tokens[token_index:])

        # If none, just append the current token and move to the next
        if len(prefix_matches) == 0:
            tokens_deid.append(token)
            continue

        # Else annotate the longest sequence as residence
        else:
            max_list = max(prefix_matches, key=len)
            tokens_deid.append("<LOCATIE {}>".format(join_tokens(max_list)))
            token_index += len(max_list)-1

    # Return the de-identified text
    return join_tokens(tokens_deid)

def annotate_institution(text):
    """ Annotate institutions """

    # Tokenize, and make a list of non-capitalized tokens (used for matching)
    tokens = tokenize_split(text)
    tokens_lower = [x.lower() for x in tokens]
    tokens_deid = []
    token_index = -1

    # Iterate over all tokens
    while token_index < len(tokens)-1:

        # Current token position and token
        token_index = token_index+1
        token = tokens[token_index]

        # Find all tokens that are prefixes of the remainder of the lowercasetext
        prefix_matches = INSTITUTION_TRIE.find_all_prefixes(tokens_lower[token_index:])

        # If none, just append the current token and move to the next
        if len(prefix_matches) == 0:
            tokens_deid.append(token)
            continue

        # Else annotate the longest sequence as institution
        else:
            max_list = max(prefix_matches, key=len)
            tokens_deid.append("<INSTELLING {}>".format(join_tokens(max_list)))
            token_index += len(max_list)-1

    # Return
    text = join_tokens(tokens_deid)

    # Detect the word "Altrecht" followed by a capitalized word
    text = re.sub("<INSTELLING altrecht>((\s[A-Z]{1}([\w]*))*)",
                  "<INSTELLING altrecht" + "\\1".lower() + ">",
                  text)

    # Return the text
    return text

### Other annotation is done using a selection of finely crafted
### (but alas less finely documented) regular expressions.
def annotate_date(text):
    """ Annotate dates """
    text = re.sub("(([1-9]|0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012]|[1-9])([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)(?![^<]*>)",
                  "<DATUM \\1> ",
                  text)

    text = re.sub("(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)(?![^<]*>)",
                  "<DATUM \\1> ",
                  text)
    return text

def annotate_age(text):
    """ Annotate ages """
    text = re.sub("(\d{1,3})([ -](jarige|jarig|jaar))(?![^<]*>)",
                  "<LEEFTIJD \\1>\\2",
                  text)
    return text

def annotate_phonenumber(text):
    """ Annotate phone numbers """
    text = re.sub("(((0)[1-9]{2}[0-9][-]?[1-9][0-9]{5})|((\\+31|0|0031)[1-9][0-9][-]?[1-9][0-9]{6}))(?![^<]*>)",
                  "<TELEFOONNUMMER \\1>",
                  text)

    text = re.sub("(((\\+31|0|0031)6){1}[-]?[1-9]{1}[0-9]{7})(?![^<]*>)",
                  "<TELEFOONNUMMER \\1>",
                  text)

    text = re.sub("((\(\d{3}\)|\d{3})\s?\d{3}\s?\d{2}\s?\d{2})(?![^<]*>)",
                  "<TELEFOONNUMMER \\1>",
                  text)

    return text

def annotate_patientnumber(text):
    """ Annotate patient numbers """
    text = re.sub("(\d{7})(?![^<]*>)",
                  "<PATIENTNUMMER \\1>",
                  text)
    return text

def annotate_postalcode(text):
    """ Annotate postal codes """
    text = re.sub("(((\d{4} [A-Z]{2})|(\d{4}[a-zA-Z]{2})))(?P<n>\W)(?![^<]*>)",
                  "<LOCATIE \\1> ",
                  text)

    text = re.sub("<LOCATIE\s(.+mg)>",
                  "\\1",
                  text)

    text = re.sub("([Pp]ostbus\s\d{5})",
                  "<LOCATIE \\1>",
                  text)
    return text

def annotate_address(text):
    """ Annotate addresses """
    text = re.sub(r"([A-Z]\w+(straat|laan|hof|plein|plantsoen|gracht|kade|weg|steeg|steeg|pad|dijk|baan|dam|dreef|kade|markt|park|plantsoen|singel|bolwerk)[\s\n\r]((\d+){1,6}(\w{0,2}){0,1}|(\d+){0,6}))",
                  "<LOCATIE \\1>",
                  text)

    return text

def annotate_email(text):
    """ Annotate emails """
    text = re.sub("(([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?))(?![^<]*>)",
                  "<URL \\1>",
                  text)

    return text

def annotate_url(text):
    """ Annotate urls """
    text = re.sub("((?!mailto:)(?:(?:http|https|ftp)://)(?:\\S+(?::\\S*)?@)?(?:(?:(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}(?:\\.(?:[0-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))|(?:(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)(?:\\.(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)*(?:\\.(?:[a-z\\u00a1-\\uffff]{2,})))|localhost)(?::\\d{2,5})?(?:(/|\\?|#)[^\\s]*)?)(?![^<]*>)",
                  "<URL \\1>",
                  text)

    text = re.sub("([\w\d\.-]{3,}(\.)(nl|com|net|be)(/[^\s]+){,1})(?![^<]*>)",
                  "<URL \\1>",
                  text)

    return text
