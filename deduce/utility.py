def any_in_text(match_list: list[str], term: str) -> bool:
    """Check if any of the strings in matchlist are in the string term"""
    return any(m in term for m in match_list)
