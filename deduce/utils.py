import importlib
import re
from typing import Any, Optional

from rapidfuzz.distance import DamerauLevenshtein


def any_in_text(match_list: list[str], term: str) -> bool:
    """
    Check if any of the strings in matchlist are in the term.

    Args:
        match_list: A list of strings to match.
        term: A string to match against.

    Returns:
        ``True`` if any of the terms in match list are contained in the term,
        ``False`` otherwise.
    """
    return any(m in term for m in match_list)


def str_match(str_1: str, str_2: str, max_edit_distance: Optional[int] = None) -> bool:
    """
    Match two strings.

    Args:
        str_1: The first string.
        str_2: The second string.
        max_edit_distance: Max edit distance between the two strings. Will use
        exact matching if argument is not used.

    Returns:
        ``True`` if the strings match, ``False`` otherwise.
    """
    if max_edit_distance is not None:
        return (
            DamerauLevenshtein.distance(str_1, str_2, score_cutoff=max_edit_distance)
            <= max_edit_distance
        )

    return str_1 == str_2


def class_for_name(module_name: str, class_name: str) -> Any:
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


def import_and_initialize(args: dict, extras: dict) -> Any:
    """
    Import and initialize a module as defined in the args config. This dictionary should
    contain a ``module`` and ``class`` key, which is imported. Any other arguments in
    args are passed to the class initializer. Any items in extras are passed to the
    class initializer if they are present.

    Args:
        args: The arguments to pass to the initalizer.
        extras: A superset of arguments that should be passed to the initializer.
        Will be checked against the class.

    Returns:
        An instantiated class, with the relevant argumetns and extras.
    """

    cls = class_for_name(args.pop("module"), args.pop("class"))

    for arg_name, arg in extras.items():
        if arg_name in cls.__init__.__code__.co_varnames:
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

    Returns: A list of options that together sgement the entire string, e.g. [["Prof.",
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
