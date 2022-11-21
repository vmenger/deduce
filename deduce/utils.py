from typing import Optional

from rapidfuzz.distance import DamerauLevenshtein


def any_in_text(match_list: list[str], term: str) -> bool:
    """Check if any of the strings in matchlist are in the string term."""
    return any(m in term for m in match_list)


def str_match(str_1: str, str_2: str, max_edit_distance: Optional[int] = None) -> bool:
    if max_edit_distance is not None:
        return DamerauLevenshtein.distance(str_1, str_2, score_cutoff=max_edit_distance) <= max_edit_distance

    return str_1 == str_2
