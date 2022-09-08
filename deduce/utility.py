from typing import Union

import docdeid


def any_in_text(match_list: list[str], term: str) -> bool:
    """Check if any of the strings in matchlist are in the string term"""
    return any(m in term for m in match_list)


def get_next_token(tokens: list[docdeid.Token], i: int) -> Union[docdeid.Token, None]:

    if i == len(tokens):
        return None

    for token in tokens[i + 1 :]:

        if (
            token.text[0] == ")"
            or token.text[0] == ">"
            or any_in_text(["\n", "\r", "\t"], token.text)
        ):
            return None

        if token.text[0].isalpha():
            return token

    return None


def get_previous_token(
    tokens: list[docdeid.Token], i: int
) -> Union[docdeid.Token, None]:

    if i == 0:
        return None

    for token in tokens[i - 1 :: -1]:

        if (
            token.text[0] == "("
            or token.text[0] == "<"
            or any_in_text(["\n", "\r", "\t"], token.text)
        ):
            return None

        if token.text[0].isalpha():
            return token

    return None
