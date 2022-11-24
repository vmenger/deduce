import importlib
from typing import Any, Optional

from rapidfuzz.distance import DamerauLevenshtein


def any_in_text(match_list: list[str], term: str) -> bool:
    """
    Check if any of the strings in matchlist are in the term.

    Args:
        match_list: A list of strings to match.
        term: A string to match against.

    Returns:
        ``True`` if any of the terms in match list are contained in the term, ``False`` otherwise.
    """
    return any(m in term for m in match_list)


def str_match(str_1: str, str_2: str, max_edit_distance: Optional[int] = None) -> bool:
    """
    Match two strings.

    Args:
        str_1: The first string.
        str_2: The second string.
        max_edit_distance: Max edit distance between the two strings. Will use exact matching if argument is not used.

    Returns:
        ``True`` if the strings match, ``False`` otherwise.
    """
    if max_edit_distance is not None:
        return DamerauLevenshtein.distance(str_1, str_2, score_cutoff=max_edit_distance) <= max_edit_distance

    return str_1 == str_2


def class_for_name(module_name: str, class_name: str) -> Any:
    """
    Will return the class by name.

    Args:
        module_name: The module where the class can be found.
        class_name: The class name.

    Returns:
        The class.
    """

    m = importlib.import_module(module_name)
    return getattr(m, class_name)
