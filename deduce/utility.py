""" This module contains all kinds of utility functionality """

import re
import codecs
import os

from nltk.metrics import edit_distance
from functools import reduce


class Annotation:
    def __init__(self, start_ix: int, end_ix: int, tag: str, text: str):
        self.start_ix = start_ix
        self.end_ix = end_ix
        self.tag = tag
        self.text_ = text

    def __eq__(self, other):
        return isinstance(other, Annotation) and self.start_ix == other.start_ix and self.end_ix == other.end_ix and \
               self.tag == other.tag and self.text_ == other.text_

    def __repr__(self):
        return self.tag + "[" + str(self.start_ix) + ":" + str(self.end_ix) + "]"

def merge_triebased(tokens, trie):
    """
    This function merges all sublists of tokens that occur in the trie to one element
    in the list of tokens. For example: if the tree contains ["A", "1"],
    then in the list of tokens ["Patient", "is", "opgenomen", "op", "A", "1"]  the sublist
    ["A", "1"] can be found in the Trie and will thus be merged,
    resulting in ["Patient", "is", "opgenomen", "op", "A1"]
    """

    # Return this list
    tokens_merged = []
    i = 0

    # Iterate over tokens
    while i < len(tokens):

        # Check for each item until the end if there are prefixes of the list in the Trie
        prefix_matches = trie.find_all_prefixes(tokens[i:])

        # If no prefixes are in the Trie, append the first token and move to the next one
        if len(prefix_matches) == 0:
            tokens_merged.append(tokens[i])
            i += 1

        # Else check the maximum length list of tokens, append it to the list that will be returned,
        # and then skip all the tokens in the list
        else:
            max_list = max(prefix_matches, key=len)
            tokens_merged.append("".join(max_list))
            i += len(max_list)

    # Return the list
    return tokens_merged

def type_of(char):
    """ Determines whether a character is alpha, a fish hook, or other """

    if char.isalpha():
        return "alpha"
    elif char == "<" or char == ">":
        return "hook"
    else:
        return "other"

def any_in_text(matchlist, token):
    """ Check if any of the strings in matchlist are in the string token """
    return reduce(lambda x, y : x | y, map(lambda x : x in token, matchlist))

def context(tokens, i):
    """ Determine next and previous tokens that start with an alpha character """

    # Find the next token
    k = i+1
    next_token = ""

    # Iterate over tokens after this one
    while k < len(tokens):

        # If any of these are found, no next token can be returned
        if tokens[k][0] == ")" or any_in_text(["\n", "\r", "\t"], tokens[k]):
            next_token = ""
            break

        # Else, this is the next token
        if tokens[k][0].isalpha() or tokens[k][0] == "<":
            next_token = tokens[k]
            break

        # If no token is found at this position, check the next
        k += 1

    # Index of the next token is simply the last checked position
    next_token_index = k

    # Find the previous token in a similar way
    k = i-1
    previous_token = ""

    # Iterate over all previous tokens
    while k >= 0:

        if tokens[k][0] == "(" or any_in_text(["\n", "\r", "\t"], tokens[k]):
            previous_token = ""
            break

        if tokens[k][0].isalpha() or tokens[k][0] == "<":
            previous_token = tokens[k]
            break

        k -= 1

    previous_token_index = k

    # Return the appropriate information in a 4-tuple
    return(previous_token, previous_token_index, next_token, next_token_index)

def is_initial(token):
    """
    Check if a token is an initial
    This is defined as:
        - Length 1 and capital
        - Already annotated initial
    """
    return ((len(token) == 1 and token[0].isupper()) or
            "INITI" in token)

def flatten_text(text):
    """
    Flattens all tags in a piece of text; e.g. tags like <INITIAL A <NAME Surname>>
    are flattened to <INITIALNAME A Surname>. This function only works for text wich
    has annotated person names, and not for other PHI categories!
    """

    # Find all tags and sort them by length, so that the longest tags are flattened first
    # This makes sure that the replacing the tag with the flattened equivalent never
    # accidentally replaces a shorter tag, for example <NAME Surname> in the example.
    to_flatten = find_tags(text)
    to_flatten.sort(key=lambda x: -len(x))

    # For each tag
    for tag in to_flatten:

        # Use the flatten method to return a tuple of tagname and value
        tagname, value = flatten(tag)

        # If any of the tags contains "PAT" it concerns the patient,
        # otherwise it concerns a random person
        if "PAT" in tagname:
            tagname = "PATIENT"
        else:
            tagname = "PERSOON"

        # Replace the found tag with the new, flattened tag
        text = text.replace(tag, "<{} {}>".format(tagname, value.strip()))

    # Make sure adjacent tags are joined together (like <INITIAL A><PATIENT Surname>),
    # optionally with a whitespace, period, hyphen or comma between them.
    # This works because all adjacent tags concern names
    # (remember that the function flatten_text() can only be used for names)!
    text = re.sub("<([A-Z]+)\s([\w\.\s,]+)>([\.\s\-,]+)[\.\s]*<([A-Z]+)\s([\w\.\s,]+)>",
                  "<\\1\\4 \\2\\3\\5>",
                  text)

    # Find all names of tags, to replace them with either "PATIENT" or "PERSOON"
    tagnames = re.findall("<([A-Z]+)", text)

    # Iterate over all tags
    for tag in tagnames:

        # If "PATIENT" is in any of them, they concern a patient
        if "PATIENT" in tag:
            text = re.sub(tag, "PATIENT", text)

        # Otherwise, they concern a person
        else:
            text = re.sub(tag, "PERSOON", text)

    # Return the text with all replacements
    return text

def flatten(tag):

    """
    Recursively flattens one tag to a tuple of name and value using splitTag() method.
    For example, the tag <INITIAL A <NAME Surname>> will be returned (INITIALNAME, A Surname)
    Returns a tuple (name, value).
    """

    # Base case, where no fishhooks are present
    if "<" not in tag:
        return ("", tag)

    # Otherwise
    else:

        # Remove fishhooks from tag
        tag = tag[1:-1]

        # Split on whitespaces
        tagspl = tag.split(" ", 1)

        # Split on the first whitespace, so we can distinguish between name and rest
        tagname = tagspl[0]
        tagrest = tagspl[1]

        # Output is initially empty
        tagvalue = ""

        # Recurse on the rest of the tag
        for tag_part in split_tags(tagrest):

            # Flatten for each value in tagrest
            flattened_tagname, flattened_tagvalue = flatten(tag_part)

            # Simply append to tagnames and values
            tagname += flattened_tagname
            tagvalue += flattened_tagvalue

        # Return pair
        return (tagname, tagvalue)

def find_tags(text):
    """ Finds and returns a list of all tags in a piece of text """

    # Helper variables
    nest_depth = 0
    startpos = 0

    # Return this list
    toflatten = []

    # Iterate over all characters
    for index, value in enumerate(text):

        # If an opening hook is encountered
        if text[index] == "<":

            # If the tag is not nested, new startposition
            if nest_depth == 0:
                startpos = index

            # Increase nest_depth
            nest_depth += 1

        # If an closing hook is encountered
        if text[index] == ">":

            # Always decrease nest_depth
            nest_depth -= 1

            # If the tag was not nested, add the tag to the return list
            if nest_depth == 0:
                toflatten.append(text[startpos:index+1])

    # Return list
    return toflatten

def split_tags(text):
    """
    Splits a text on normal text and tags, for example "This is text with a <NAME name> in it"
    will     return: ["This is text with a ", "<NAME name>", " in it"]. Nested tags will be
    regarded as one tag.  This function can be used on text as a whole,
    but is more appropriately used in the value part of nested tags
    """

    # Helper variables
    nest_depth = 0
    startpos = 0

    # Return this list
    splitbytags = []

    # Iterate over all characters
    for index, value in enumerate(text):

        # If an opening hook is encountered
        if text[index] == "<":

            # Split if the tag is not nested
            if nest_depth == 0:
                splitbytags.append(text[startpos:index])
                startpos = index

            # Increase the nest_depth
            nest_depth += 1

        # If a closing hook is encountered
        if text[index] == ">":

            # First decrease the nest_depth
            nest_depth -= 1

            # Split if the tag was not nested
            if nest_depth == 0:
                splitbytags.append(text[startpos:index+1])
                startpos = index+1

    # Append the last characters
    splitbytags.append(text[startpos:])

    # Filter empty elements in the list (happens for example when <tag><tag> occurs)
    return([x for x in splitbytags if len(x) > 0])


def get_data(path):
    """ Define where to find the data files """
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', path)

def _normalize_value(line):
    """ Removes all non-ascii characters from a string """
    return unicodedata.normalize('NFKD', unicode(line)).encode("ascii", "ignore")

def read_list(list_name, encoding='utf-8', lower=False,
              strip=True, min_len=None, normalize=None, unique=True):
    """ Read a list from file and return the values. """

    data = codecs.open(get_data(list_name), encoding=encoding)

    if normalize == "ascii":
        data = [_normalize_value(line) for line in data]

    if lower:
        data = [line.lower() for line in data]

    if strip:
        data = [line.strip() for line in data]

    if min_len:
        data = [line for line in data if len(line) >= min_len]

    if unique:
        data_nodoubles = list(set(data))

    return data_nodoubles

def parse_tag(tag: str) -> tuple:
    """
    Parse a Deduce-style tag into its tag proper and its text. Does not handle nested tags
    :param tag: the Deduce-style tag, for example, <VOORNAAMONBEKEND Peter>
    :return: the tag type and text, for example, ("VOORNAAMONBEKEND", "Peter")
    """
    split_ix = tag.index(" ")
    return tag[1:split_ix], tag[split_ix+1:len(tag)-1]

def get_annotations(annotated_text: str, tags: list, n_leading_whitespaces=0) -> list:
    """
    Find structured annotations from tags, with indices pointing to the original text. ***Does not handle nested tags***
    :param annotated_text: the annotated text
    :param tags: the tags found in the text, listed in the order they appear in the text
    :param n_leading_whitespaces: the number of leading whitespaces in the raw text
    :return: the annotations with indices corresponding to the original (raw) text;
    this accounts for string stripping during annotation
    """
    ix = 0
    annotations = []
    raw_text_ix = n_leading_whitespaces
    for tag in tags:
        tag_ix = annotated_text.index(tag, ix) - ix
        tag_type, tag_text = parse_tag(tag)
        annotations.append(Annotation(raw_text_ix + tag_ix, raw_text_ix + tag_ix + len(tag_text), tag_type, tag_text))
        ix += (tag_ix + len(tag))
        raw_text_ix += (tag_ix + len(tag_text))
    return annotations

def get_first_non_whitespace(text: str) -> int:
    return text.index(text.lstrip()[0])
