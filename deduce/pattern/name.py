from abc import ABC
from typing import Optional

import docdeid as dd


class TokenPatternWithLookup(dd.TokenPattern, ABC):
    def __init__(self, lookup_sets: dd.ds.DsCollection[dd.ds.LookupSet], *args, **kwargs) -> None:
        self._lookup_sets = lookup_sets
        super().__init__(*args, **kwargs)


class PrefixWithNamePattern(TokenPatternWithLookup):
    def token_precondition(self, token: dd.Token) -> bool:

        return token.next() is not None

    def match(self, token: dd.Token, metadata: Optional[dd.MetaData] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        if (
            token.text.lower() in self._lookup_sets["prefixes"]
            and token.next().text[0].isupper()
            and token.next().text not in self._lookup_sets["whitelist"]
        ):

            return token, token.next()

        return None


class InterfixWithNamePattern(TokenPatternWithLookup):
    def token_precondition(self, token: dd.Token) -> bool:

        return token.next() is not None

    def match(self, token: dd.Token, metadata: Optional[dd.MetaData] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        if (
            token.text.lower() in self._lookup_sets["interfixes"]
            and token.next().text in self._lookup_sets["interfix_surnames"]
            and token.next().text not in self._lookup_sets["whitelist"]
        ):

            return token, token.next()

        return None


class InitialWithCapitalPattern(TokenPatternWithLookup):
    def token_precondition(self, token: dd.Token) -> bool:

        return token.next() is not None

    def match(self, token: dd.Token, metadata: Optional[dd.MetaData] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        if (
            token.text[0].isupper()
            and len(token) == 1
            and len(token.next()) > 3
            and token.next().text[0].isupper()
            and token.next().text not in self._lookup_sets["whitelist"]
        ):

            return token, token.next()

        return None


class InitiaalInterfixCapitalPattern(TokenPatternWithLookup):
    def token_precondition(self, token: dd.Token) -> bool:

        return (token.previous() is not None) and (token.next() is not None)

    def match(self, token: dd.Token, metadata: Optional[dd.MetaData] = None) -> Optional[tuple[dd.Token, dd.Token]]:
        if (
            token.previous().text[0].isupper()
            and len(token.previous()) == 1
            and token.next().text[0].isupper()
            and token.text in self._lookup_sets["interfixes"]
        ):

            return token.previous(), token.next()

        return None


class FirstNameLookupPattern(TokenPatternWithLookup):
    def match(self, token: dd.Token, metadata: Optional[dd.MetaData] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        if token.text in self._lookup_sets["first_names"] and token.text not in self._lookup_sets["whitelist"]:

            return token, token

        return None


class SurnameLookupPattern(TokenPatternWithLookup):
    def match(self, token: dd.Token, metadata: Optional[dd.MetaData] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        if token.text in self._lookup_sets["surnames"] and token.text not in self._lookup_sets["whitelist"]:

            return token, token

        return None
