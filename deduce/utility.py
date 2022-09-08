""" This module contains all kinds of utility functionality """

import re
from functools import reduce
from typing import Union
import docdeid


def any_in_text(matchlist, token):
    """Check if any of the strings in matchlist are in the string token"""
    return reduce(lambda x, y: x | y, map(lambda x: x in token, matchlist))


def get_next_token(tokens: list[docdeid.Token], i: int) -> Union[docdeid.Token, None]:

    if i == len(tokens):
        return None

    for token in tokens[i + 1 :]:

        if token.text[0] == ")" or token.text[0] == '>' or any_in_text(["\n", "\r", "\t"], token.text):
            return None

        if token.text[0].isalpha():
            return token

    return None


def get_previous_token(tokens: list[docdeid.Token], i: int) -> Union[docdeid.Token, None]:

    if i == 0:
        return None

    for token in tokens[i-1::-1]:

        if token.text[0] == "(" or token.text[0] == '<' or any_in_text(["\n", "\r", "\t"], token.text):
            return None

        if token.text[0].isalpha():
            return token

    return None


def is_initial(token):
    """
    Check if a token is an initial
    This is defined as:
        - Length 1 and capital
        - Already annotated initial
    """
    return (len(token) == 1 and token[0].isupper()) or "INITI" in token


def find_tags(text):
    """Finds and returns a list of all tags in a piece of text"""

    # Helper variables
    nest_depth = 0
    startpos = 0

    # Return this list
    toflatten = []

    # Iterate over all characters
    for index, _ in enumerate(text):

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
                toflatten.append(text[startpos : index + 1])

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
    for index, _ in enumerate(text):

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
                splitbytags.append(text[startpos : index + 1])
                startpos = index + 1

    # Append the last characters
    splitbytags.append(text[startpos:])

    # Filter empty elements in the list (happens for example when <tag><tag> occurs)
    return [x for x in splitbytags if len(x) > 0]


def parse_tag(tag: str) -> tuple:
    """
    Parse a Deduce-style tag into its tag proper and its text. Does not handle nested tags
    :param tag: the Deduce-style tag, for example, <VOORNAAMONBEKEND Peter>
    :return: the tag type and text, for example, ("VOORNAAMONBEKEND", "Peter")
    """
    split_ix = tag.index(" ")
    return tag[1:split_ix], tag[split_ix + 1 : len(tag) - 1]


def get_annotations(
    annotated_text: str, tags: list, n_leading_whitespaces=0
) -> list[docdeid.Annotation]:
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

        annotations.append(
            docdeid.Annotation(
                tag_text,
                raw_text_ix + tag_ix,
                raw_text_ix + tag_ix + len(tag_text),
                tag_type,
            )
        )

        ix += tag_ix + len(tag)
        raw_text_ix += tag_ix + len(tag_text)
    return annotations


def get_first_non_whitespace(text: str) -> int:

    stripped_text = text.lstrip()

    if len(stripped_text) == 0:
        return len(text)
    else:
        return text.index(stripped_text[0])


def get_shift(text: str, intext_annotated: str) -> int:
    return get_first_non_whitespace(text) - get_first_non_whitespace(intext_annotated)


def get_adjacent_tags_replacement(match: re.Match) -> str:
    text = match.group(0)
    tag = match.group(1)
    left = match.group(2)
    right = match.group(3)
    start_ix = text.index(">") + 1
    end_ix = text[1:].index("<") + 1
    separator = text[start_ix:end_ix]
    return "<" + tag + " " + left + separator + right + ">"


def merge_adjacent_tags(text: str) -> str:
    """
    Adjacent tags are merged into a single tag
    :param text: the text from which you want to merge adjacent tags
    :return: the text with adjacent tags merged
    """
    while True:
        oldtext = text
        text = re.sub(
            "<([A-Z]+)\s([^>]+)>[\.\s\-,]?[\.\s]?<\\1\s([^>]+)>",
            get_adjacent_tags_replacement,
            text,
        )
        if text == oldtext:
            break
    return text


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
