""" This module contains all kinds of utility functionality """

import codecs
import os
from deduce import utilcls
from deduce.listtrie import ListTrie
from functools import reduce

from deduce.utilcls import Token, InvalidTokenError, Annotation
import re
import unicodedata
from functools import reduce

class Annotation:
    def __init__(self, start_ix: int, end_ix: int, tag: str, text: str):
        self.start_ix = start_ix
        self.end_ix = end_ix
        self.tag = tag
        self.text_ = text

    def __eq__(self, other):
        return (
            isinstance(other, Annotation)
            and self.start_ix == other.start_ix
            and self.end_ix == other.end_ix
            and self.tag == other.tag
            and self.text_ == other.text_
        )

    def __repr__(self):
        return self.tag + "[" + str(self.start_ix) + ":" + str(self.end_ix) + "]"

def merge_tokens(tokens: list[Token]) -> Token:
    if len(tokens) == 0:
        raise InvalidTokenError("empty")
    text = "".join([el.text for el in tokens])
    start_ix = tokens[0].start_ix
    end_ix = tokens[-1].end_ix
    if any([tokens[i].start_ix < tokens[i-1].end_ix for i in range(1, len(tokens))]):
        raise InvalidTokenError("overlap")
    if any([tokens[i].start_ix != tokens[i-1].end_ix for i in range(1, len(tokens))]):
        raise InvalidTokenError("gap")
    return Token(text, start_ix, end_ix)

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
        prefix_matches = trie.find_all_prefixes([el.text for el in tokens[i:]])

        # If no prefixes are in the Trie, append the first token and move to the next one
        if len(prefix_matches) == 0:
            tokens_merged.append(tokens[i])
            i += 1

        # Else check the maximum length list of tokens, append it to the list that will be returned,
        # and then skip all the tokens in the list
        else:
            max_list = max(prefix_matches, key=len)
            merged_token = merge_tokens(tokens[i:i+len(max_list)])
            tokens_merged.append(merged_token)
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


def context(tokens, i):
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
        if tokens[k].text[0].isalpha() or tokens[k].text[0] == "<":
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

        if tokens[k].text[0].isalpha() or tokens[k].text[0] == "<":
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
    return (len(token) == 1 and token[0].isupper()) or "INITI" in token


def flatten_text_all_phi(text: str) -> str:
    """
    This is inspired by flatten_text, but works for all PHI categories
    :param text: the text in which you wish to flatten nested annotations
    :return: the text with nested annotations replaced by a single annotation with the outermost category
    """
    to_flatten = find_tags(text)
    to_flatten.sort(key=lambda x: -len(x))

    for tag in to_flatten:
        _, value = flatten(tag)
        outermost_category = parse_tag(tag)[0]
        text = text.replace(tag, f"<{outermost_category} {value.strip()}>")

    return text


def is_blank_period_hyphen_comma(text: str) -> bool:
    """
    Asserts whether a given text is made up of only whitespaces, periods, hyphens or commas in between
    :param text: the (short) text to be tested
    :return: whether the test passes
    """
    return all([el.strip() in {'', '.', ',', '-'} for el in text])

def merge_consecutive_names(text: str, annotations: list[Annotation]) -> list[Annotation]:
    """
    Make sure adjacent tags are joined together (like <INITIAL A><PATIENT Surname>),
    optionally with a whitespace, period, hyphen or comma between them.
    This works because all adjacent tags concern names
    (remember that the function flatten_text() can only be used for names)!
    :param text: the original text being annotated
    :param annotations: the annotations that you want to potentially merge
    :return: the condensed list of annotations
    """
    if len(annotations) < 2:
        return annotations.copy()
    merged_annotations = [annotations[0]]
    for ann in annotations[1:]:
        inter_text = text[merged_annotations[-1].end_ix:ann.start_ix]
        if is_blank_period_hyphen_comma(inter_text):
            merged_annotations[-1] = Annotation(merged_annotations[-1].start_ix, ann.end_ix,
                                                merged_annotations[-1].tag + ann.tag,
                                                text[merged_annotations[-1].start_ix:ann.end_ix])
        else:
            merged_annotations.append(ann)
    return merged_annotations

def flatten_text(text: str, annotations: list[Annotation]) -> list[Annotation]:
    """
    Flattens all tags in a piece of text; e.g. tags like <INITIAL A <NAME Surname>>
    are flattened to <INITIALNAME A Surname>. This function only works for text wich
    has annotated person names, and not for other PHI categories!
    """

    # Find all tags and sort them by length, so that the longest tags are flattened first
    # This makes sure that the replacing the tag with the flattened equivalent never
    # accidentally replaces a shorter tag, for example <NAME Surname> in the example.
    to_flatten = annotations.copy()

    # Now group the tags that are overlapping
    groups = group_tags(to_flatten)

    # For each group
    final_annotations = []
    for grp in groups:

        # Use the flatten method to return a tuple of tagname and value
        grouped_tag = flatten(grp)

        # If any of the tags contains "PAT" it concerns the patient,
        # otherwise it concerns a random person
        if "PAT" in grouped_tag.tag:
            tagname = "PATIENT"
        else:
            tagname = "PERSOON"

        # Replace the found tag with the new, flattened tag
        final_annotations.append(Annotation(grouped_tag.start_ix, grouped_tag.end_ix, tagname, grouped_tag.text_))

    # Make sure adjacent tags are joined together (like <INITIAL A><PATIENT Surname>),
    # optionally with a whitespace, period, hyphen or comma between them.
    # This works because all adjacent tags concern names
    # (remember that the function flatten_text() can only be used for names)!
    merged_consecutive = merge_consecutive_names(text, final_annotations)

    # Find all names of tags, to replace them with either "PATIENT" or "PERSOON"
    return [utilcls.replace_tag(ann, "PATIENT" if "PATIENT" in ann.tag else "PERSOON") for ann in merged_consecutive]

def group_tags(tags: list[Annotation]) -> list[list[Annotation]]:
    """
    Given a list of annotations, group them into lists of annotations that are overlapping
    :param tags: tags you want to look through
    :return: a list of lists, where each list is annotations that overlap with each other
    """
    sorted_tags = sorted(tags, key=lambda x: (x.start_ix, -x.end_ix))
    groups = []
    for tag in sorted_tags:
        if len(groups) == 0 or tag.start_ix >= groups[-1][0].end_ix:
            groups.append([tag])
        else:
            groups[-1].append(tag)
    return groups

def flatten(tags: list[Annotation]) -> Annotation:
    # There must be one and only one annotation that encompasses all the others
    min_start_ix = min([el.start_ix for el in tags])
    max_end_ix = max([el.end_ix for el in tags])
    encompassing_ix = [i for i,el in enumerate(tags) if el.start_ix == min_start_ix and el.end_ix == max_end_ix]
    if len(encompassing_ix) != 1:
        raise ValueError("No tag encompasses all the others uniquely")

    # Now group the remaining tags into groups that need to be flattened
    tag_groups = group_tags([el for i,el in enumerate(tags) if i != encompassing_ix[0]])

    # Now each group must be flattened into a single tag
    flattened_tag_groups = [flatten(grp) for grp in tag_groups]

    # Now we have to join the "mother" tag with all the daughter flattened tags
    encompassing_tag = tags[encompassing_ix[0]]
    return Annotation(encompassing_tag.start_ix, encompassing_tag.end_ix,
                      encompassing_tag.tag + "".join([el.tag for el in flattened_tag_groups]),
                      encompassing_tag.text_)

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


def get_first_non_whitespace(text: str) -> int:
    return text.index(text.lstrip()[0])
