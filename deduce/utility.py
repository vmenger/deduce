""" This module contains all kinds of utility functionality """

import codecs
import os
import re
import unicodedata
from functools import reduce

from deduce.utilcls import TokenGroup, Annotation


def merge_triebased(tokens: list, trie) -> list:
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
    """Determines whether a character is alpha, a fish hook, or other"""

    if char.isalpha():
        return "alpha"

    if char in ("<", ">"):
        return "hook"

    return "other"


def any_in_text(matchlist, token):
    """Check if any of the strings in matchlist are in the string token"""
    return reduce(lambda x, y: x | y, map(lambda x: x in token, matchlist))


def context(tokens: list, i):
    """Determine next and previous tokens that start with an alpha character"""

    # Find the next token
    k = i + 1
    next_token = None

    # Iterate over tokens after this one
    while k < len(tokens):

        # If any of these are found, no next token can be returned
        if tokens[k].text[0] == ")" or any_in_text(["\n", "\r", "\t"], tokens[k].text):
            next_token = None
            break

        # Else, this is the next token
        if tokens[k].text[0].isalpha() or tokens[k].is_annotation():
            next_token = tokens[k]
            break

        # If no token is found at this position, check the next
        k += 1

    # Index of the next token is simply the last checked position
    next_token_index = k

    # Find the previous token in a similar way
    k = i - 1
    previous_token = None

    # Iterate over all previous tokens
    while k >= 0:

        if tokens[k].text[0] == "(" or any_in_text(["\n", "\r", "\t"], tokens[k].text):
            previous_token = None
            break

        if tokens[k].text[0].isalpha() or tokens[k].is_annotation():
            previous_token = tokens[k]
            break

        k -= 1

    previous_token_index = k

    # Return the appropriate information in a 4-tuple
    return previous_token, previous_token_index, next_token, next_token_index


def is_initial(token):
    """
    Check if a token is an initial
    This is defined as:
        - Length 1 and capital
        - Already annotated initial
    """
    return (token.is_annotation() and 'INITI' in token.get_full_annotation()) or \
           (not token.is_annotation() and len(token.text) == 1 and token.text[0].isupper())


def flatten_text_all_phi(spans: list) -> list:
    """
    This is inspired by flatten_text, but works for all PHI categories
    :param spans: the spans in which you wish to flatten nested annotations
    :return: the text with nested annotations replaced by a single annotation with the outermost category
    """
    return [span.flatten(with_annotation=span.annotation) if span.is_annotation() else span for span in spans]

def flatten_text(tokens: list) -> list:
    """
    Flattens nested tags; e.g. tags like <INITIAL A <NAME Surname>>
    are flattened to <INITIALNAME A Surname>. This function only works for text wich
    has annotated person names, and not for other PHI categories!
    :param tokens: the list of tokens containing the annotations that need to be flattened
    :return: a new list of tokens containing only non-nested annotations
    """
    flattened = []
    for token in tokens:
        if not token.is_annotation():
            flattened.append(token)
        else:
            flattened.append(
                token.flatten(with_annotation='PATIENT' if 'PAT' in token.get_full_annotation() else 'PERSOON')
            )

    # TODO: re-use deduce.merge_adjacent_tags in this method
    # Make sure adjacent tags are joined together (like <INITIAL A><PATIENT Surname>),
    # optionally with a whitespace, period, hyphen or comma between them.
    # This works because all adjacent tags concern names
    # (remember that the function flatten_text() can only be used for names)!
    attached = []
    i = 0
    while i < len(flattened):
        span = flattened[i]
        if not span.is_annotation():
            attached.append(span)
            i += 1
            continue
        next_annotations = [j for j in range(i + 1, len(flattened)) if flattened[j].is_annotation()]
        if not next_annotations:
            attached.append(span)
            i += 1
            continue
        j = next_annotations[0]
        if re.fullmatch("<([A-Z]+)\s([\w.\s,]+)>([.\s\-,]+)[.\s]*<([A-Z]+)\s([\w.\s,]+)>", to_text(flattened[i:j+1])):
            group = TokenGroup([t.without_annotation() for t in flattened[i:j+1]],
                               flattened[i].annotation + flattened[j].annotation)
            attached.append(group)
            i = j + 1
        else:
            attached.append(span)
            i += 1

    # Find all names of tags, to replace them with either "PATIENT" or "PERSOON"
    replaced = [token.with_annotation('PATIENT' if 'PATIENT' in token.get_full_annotation() else 'PERSOON')
                if token.is_annotation()
                else token
                for token in attached]

    # Return the text with all replacements
    return replaced


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


def get_data(path):
    """Define where to find the data files"""
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", path)


def _normalize_value(line):
    """Removes all non-ascii characters from a string"""
    line = str(bytes(line, encoding="ascii", errors="ignore"), encoding="ascii")
    return unicodedata.normalize("NFKD", line)


def read_list(
    list_name,
    encoding="utf-8",
    lower=False,
    strip=True,
    min_len=None,
    normalize=None,
    unique=True,
):
    """Read a list from file and return the values."""

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
    else:
        return data

    return data_nodoubles


def parse_tag(tag: str) -> tuple:
    """
    Parse a Deduce-style tag into its tag proper and its text. Does not handle nested tags
    :param tag: the Deduce-style tag, for example, <VOORNAAMONBEKEND Peter>
    :return: the tag type and text, for example, ("VOORNAAMONBEKEND", "Peter")
    """
    split_ix = tag.index(" ")
    return tag[1:split_ix], tag[split_ix + 1 : len(tag) - 1]


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
        annotations.append(
            Annotation(
                raw_text_ix + tag_ix,
                raw_text_ix + tag_ix + len(tag_text),
                tag_type,
                tag_text,
            )
        )
        ix += tag_ix + len(tag)
        raw_text_ix += tag_ix + len(tag_text)
    return annotations


def to_text(tokens: list) -> str:
    return ''.join([token.as_text() for token in tokens])
