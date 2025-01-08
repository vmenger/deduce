import importlib
import inspect
import json
import re
from pathlib import Path
from typing import Optional, Union

import docdeid as dd
from docdeid import Tokenizer
from docdeid.str import LowercaseTail
from rapidfuzz.distance import DamerauLevenshtein

_TITLECASER = LowercaseTail()


def str_match(
    str_1: str,
    str_2: str,
    max_edit_distance: Optional[int] = None,
    titlecase: bool = True,
) -> bool:
    """
    Match two strings, potentially in a fuzzy way.

    Args:
        str_1: The first string.
        str_2: The second string.
        max_edit_distance: Max edit distance between the two strings. Will use
        exact matching if argument is not used.

    Returns:
        ``True`` if the strings match, ``False`` otherwise.
    """
    norm_1, norm_2 = (
        (_TITLECASER.process(str_1), _TITLECASER.process(str_2))
        if titlecase
        else (str_1, str_2)
    )
    if max_edit_distance is not None:
        return (
            DamerauLevenshtein.distance(norm_1, norm_2, score_cutoff=max_edit_distance)
            <= max_edit_distance
        )

    return norm_1 == norm_2


def class_for_name(module_name: str, class_name: str) -> type:
    """
    Will import and return the class by name.

    Args:
        module_name: The module where the class can be found.
        class_name: The class name.

    Returns:
        The class.
    """

    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def initialize_class(cls: type, args: dict, extras: dict) -> object:
    """
    Initialize a class. Any arguments in args are passed to the class initializer. Any
    items in extras are passed to the class initializer if they are present.

    Args:
        cls: The class to initialize.
        args: The arguments to pass to the initializer.
        extras: A superset of arguments that should be passed to the initializer.
        Will be checked against the class.

    Returns:
        An instantiated class, with the relevant arguments and extras.
    """

    cls_params = inspect.signature(cls).parameters

    for arg_name, arg in extras.items():

        if arg_name in cls_params:

            args[arg_name] = arg

    return cls(**args)


def overwrite_dict(base: dict, add: dict) -> dict:
    """
    Overwrites the items of the first dict with those of the second.

    Accepts nested dictionaries.
    """

    for key, value in add.items():
        if isinstance(value, dict):
            base[key] = overwrite_dict(base.get(key, {}), value)
        else:
            base[key] = value

    return base


def has_overlap(intervals: list[tuple]) -> bool:
    """
    Checks if there is any overlap in a list of tuples. Assumes the interval ranges from
    the first to the second element of the tuple. Any other elements are ignored.

    Args:
        intervals: The intervals, as a list of tuples

    Returns:
        True if there is any overlap between tuples, False otherwise.
    """

    intervals_sorted = sorted(intervals, key=lambda tup: tup[0])

    for i in range(len(intervals_sorted) - 1):
        if intervals_sorted[i][1] > intervals_sorted[i + 1][0]:
            return True

    return False


def repl_segments(s: str, matches: list[tuple]) -> list[list[str]]:
    """
    Segment a string into consecutive substrings, with one or more options for each
    substring.

    Args:
        s: The input string.
        matches: A list of matches, consisting of a tuple with start- and end char,
            followed by a list of options for that substring, e.g.
            (5, 8, ["Mr.", "Meester"]).

    Returns:
        A list of options that together segment the entire string, e.g. [["Prof.",
        "Professor"], [" "], ["Meester", "Mr."], [" Lievenslaan"]].
    """

    if len(matches) == 0:
        return [[s]]

    choices = []
    pos = 0

    for match in sorted(matches, key=lambda tup: tup[0]):
        if pos != match[0]:
            choices.append([s[pos : match[0]]])

        choices.append(match[2])
        pos = match[1]

    if matches[-1][1] != len(s):
        choices.append([s[pos : len(s)]])

    return choices


def str_variations(s: str, repl: dict[str, list[str]]) -> list[str]:
    """
    Gets all possible textual variations of a string, by combining any subset of
    replacements defined in the `repl` dictionary. E.g.: the input string
    'Prof. Mr. Lievenslaan' combined with the mapping {'Prof.': ['Prof.',
    'Professor'], 'Mr.': ['Mr.', 'Meester']} will result in the following
    variations: ['Prof. Mr. Lievenslaan', 'Professor Mr. Lievenslaan', 'Prof.
    Meester Lievenslaan', 'Professor Meester Lievenslaan'].

    Args:
        s: The input string
        repl: A mapping of substrings to one or multiple replacements, e.g.
            {'Professor': ['Professor', 'Prof.', 'prof.']}. The key will be matched
            using `re.finditer`, so both literal phrases and  regular expressions
            can be used.

    Returns:
        A list containing all possible textual variations.
    """

    matches = []

    for pattern in repl:
        for m in re.finditer(pattern, s):
            matches.append((m.span()[0], m.span()[1], repl[pattern]))

    if len(matches) == 0:
        return [s]

    if has_overlap(matches):
        raise RuntimeError(
            "Cannot explode input string, because there is overlap "
            "in the replacement mapping."
        )

    variations = [""]

    for segment in repl_segments(s, matches):
        new_variations = []
        for choice in segment:
            for prefix in variations:
                new_variations.append(prefix + choice)
        variations = new_variations

    return variations


def apply_transform(items: set[str], transform_config: dict) -> set[str]:
    """
    Applies a transformation to a set of items.

    Args:
        items: The input items.
        transform_config: The transformation, including configuration (see
        transform.json for examples).

    Returns: The transformed items.
    """

    strip_lines = transform_config.get("strip_lines", True)
    transforms = transform_config.get("transforms", {})

    for _, transform in transforms.items():

        to_add = []

        for item in items:
            # FIXME Why _add_ the result of `str_variations` rather than
            #   replace the original item? In most cases, manual effort was
            #   exerted to include also the original string in
            #   the replacements, however some transformations do not include
            #   it (e.g. for "(?<=\\()Ut(?=\\))", the surrounding parens are
            #   always dropped). I guess that these transformations do not
            #   include the original version because it's supposed to be
            #   dropped. Or if the original version ("(Ut)" in this case) was
            #   supposed to be kept, by not including it explicitly yet
            #   _adding_ all variations to the set of terms, the net effect is
            #   that just all _other_ transformations within the string will
            #   be excluded in the version that keeps the original "(Ut)".
            #
            #   We should either avoid combining the result of `str_variations`
            #   with the original set, `{item}`, or _always_ apply the void
            #   transformation so as to save effort in writing
            #   the `transform.json` configs and prevent subtle bugs.
            to_add += str_variations(item, transform)

        items.update(to_add)

    if strip_lines:
        items = {i.strip() for i in items}

    return items


def optional_load_items(path: Path) -> Optional[set[str]]:
    """
    Load items (lines) from a textfile, returning None if file does not exist.

    Args:
        path: The full path to the file.

    Returns: The lines of the file as a set if the file exists, None otherwise.
    """

    try:
        with open(path, "r", encoding="utf-8") as file:
            items = {line.strip() for line in file.readlines()}
    except FileNotFoundError:
        return None

    return items


def optional_load_json(path: Path) -> Optional[dict]:
    """
    Load json, returning None if file does not exist.

    Args:
        path: The full path to the file.

    Returns: The json data as a dict if the file exists, None otherwise.
    """

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return None

    return data


def lookup_set_to_trie(
    lookup_set: dd.ds.LookupSet, tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """
    Converts a LookupSet into an equivalent LookupTrie.

    Args:
        lookup_set: The input LookupSet
        tokenizer: The tokenizer used to create sequences

    Returns: A LookupTrie with the same items and matching pipeline as the
    input LookupSet.
    """

    trie = dd.ds.LookupTrie(matching_pipeline=lookup_set.matching_pipeline)

    for item in lookup_set.items():
        trie.add_item([token.text for token in tokenizer.tokenize(item)])

    return trie


def ensure_path(path_or_str: Union[str, Path]) -> Path:
    """Casts the argument as a `Path` if it's not a `Path` already."""
    return path_or_str if isinstance(path_or_str, Path) else Path(path_or_str)
