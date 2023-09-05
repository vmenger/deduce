from abc import ABC
from typing import Optional

import docdeid as dd


class TokenPatternWithLookup(dd.TokenPattern, ABC):
    """Extends a general ``TokenPattern`` by adding a lookup set attribute, that can be used in pattern logic."""

    def __init__(self, lookup_sets: dd.ds.DsCollection[dd.ds.LookupSet], *args, **kwargs) -> None:
        self._lookup_sets = lookup_sets
        super().__init__(*args, **kwargs)



class InitialWithCapitalPattern(TokenPatternWithLookup):
    """Matches an initial followed by an titlecase word with at least 3 characters."""

    def token_precondition(self, token: dd.Token) -> bool:
        return token.next_alpha() is not None

    def match(self, token: dd.Token, metadata: dd.MetaData) -> Optional[tuple[dd.Token, dd.Token]]:
        if (
            token.text[0].isupper()
            and len(token) == 1
            and len(token.next_alpha()) > 3
            and token.next_alpha().text[0].isupper()
            and token.next_alpha().text not in self._lookup_sets["whitelist"]
        ):

            return token, token.next_alpha()

        return None


class InitiaalInterfixCapitalPattern(TokenPatternWithLookup):
    """Matches an initial, followed by an interfix, followed by a titlecase word."""

    def token_precondition(self, token: dd.Token) -> bool:
        return (token.previous_alpha() is not None) and (token.next_alpha() is not None)

    def match(self, token: dd.Token, metadata: dd.MetaData) -> Optional[tuple[dd.Token, dd.Token]]:
        if (
            token.previous_alpha().text[0].isupper()
            and len(token.previous_alpha()) == 1
            and token.next_alpha().text[0].isupper()
            and token.text in self._lookup_sets["interfixes"]
        ):

            return token.previous_alpha(), token.next_alpha()

        return None


class FirstNameLookupPattern(TokenPatternWithLookup):
    """Matches first names, based on lookup."""

    def match(self, token: dd.Token, metadata: dd.MetaData) -> Optional[tuple[dd.Token, dd.Token]]:
        if token.text in self._lookup_sets["first_names"] and token.text not in self._lookup_sets["whitelist"]:

            return token, token

        return None


class SurnameLookupPattern(TokenPatternWithLookup):
    """Matches surnames, based on lookup."""

    def match(self, token: dd.Token, metadata: dd.MetaData) -> Optional[tuple[dd.Token, dd.Token]]:
        if token.text in self._lookup_sets["surnames"] and token.text not in self._lookup_sets["whitelist"]:

            return token, token

        return None
