from abc import ABC
from typing import Optional

import docdeid as dd


class TokenPatternWithLookup(dd.TokenPattern, ABC):
    """Extends a general ``TokenPattern`` by adding a lookup set attribute, that can be used in pattern logic."""

    def __init__(self, lookup_sets: dd.ds.DsCollection[dd.ds.LookupSet], *args, **kwargs) -> None:
        self._lookup_sets = lookup_sets
        super().__init__(*args, **kwargs)


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
