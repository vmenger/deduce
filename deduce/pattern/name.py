from abc import ABC
from typing import Optional

import docdeid
from docdeid.pattern.pattern import TokenPattern
from rapidfuzz.distance import DamerauLevenshtein


def str_match(str_1: str, str_2: str, max_edit_distance: Optional[int] = None) -> bool:

    if max_edit_distance is not None:
        return DamerauLevenshtein.distance(str_1, str_2, score_cutoff=max_edit_distance) <= max_edit_distance

    return str_1 == str_2


class TokenPatternWithLookup(TokenPattern, ABC):
    def __init__(self, lookup_sets: docdeid.DsCollection[docdeid.LookupSet], *args, **kwargs) -> None:
        self._lookup_sets = lookup_sets
        super().__init__(*args, **kwargs)


class PrefixWithNamePattern(TokenPatternWithLookup):
    def token_precondition(self, token: docdeid.Token) -> bool:

        return token.next() is not None

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.text.lower() in self._lookup_sets["prefixes"]
            and token.next().text[0].isupper()
            and token.next().text not in self._lookup_sets["whitelist"]
        ):

            return token, token.next()

        return None


class InterfixWithNamePattern(TokenPatternWithLookup):
    def token_precondition(self, token: docdeid.Token) -> bool:

        return token.next() is not None

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.text.lower() in self._lookup_sets["interfixes"]
            and token.next().text in self._lookup_sets["interfix_surnames"]
            and token.next().text not in self._lookup_sets["whitelist"]
        ):

            return token, token.next()

        return None


class InitialWithCapitalPattern(TokenPatternWithLookup):
    def token_precondition(self, token: docdeid.Token) -> bool:

        return token.next() is not None

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

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
    def token_precondition(self, token: docdeid.Token) -> bool:

        return (token.previous() is not None) and (token.next() is not None)

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:
        if (
            token.previous().text[0].isupper()
            and len(token.previous()) == 1
            and token.next().text[0].isupper()
            and token.text in self._lookup_sets["interfixes"]
        ):

            return token.previous(), token.next()

        return None


class FirstNameLookupPattern(TokenPatternWithLookup):
    # TODO: make this a separate annotator class

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if token.text in self._lookup_sets["first_names"] and token.text not in self._lookup_sets["whitelist"]:

            return token, token

        return None


class SurnameLookupPattern(TokenPatternWithLookup):
    # TODO: make this a separate annotator class

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if token.text in self._lookup_sets["surnames"] and token.text not in self._lookup_sets["whitelist"]:

            return token, token

        return None


class PersonFirstNamePattern(TokenPattern):
    def doc_precondition(self, doc: docdeid.Document) -> bool:

        patient = doc.get_metadata_item("patient")
        return (patient is not None) and (patient.first_names is not None)

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        for first_name in metadata["patient"].first_names:

            if str_match(token.text, first_name) or (
                len(token.text) > 3 and str_match(token.text, first_name, max_edit_distance=1)
            ):

                return token, token

        return None


class PersonInitialFromNamePattern(TokenPattern):
    def doc_precondition(self, doc: docdeid.Document) -> bool:

        patient = doc.get_metadata_item("patient")
        return (patient is not None) and (patient.first_names is not None)

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        for _, first_name in enumerate(metadata["patient"].first_names):

            if str_match(token.text, first_name[0]):

                next_token = token.next()

                if (next_token is not None) and str_match(next_token.text, "."):
                    return token, next_token

                return token, token

        return None


class PersonSurnamePattern(TokenPattern):
    def __init__(self, tokenizer: docdeid.BaseTokenizer, *args, **kwargs) -> None:
        self._tokenizer = tokenizer
        super().__init__(*args, **kwargs)

    def doc_precondition(self, doc: docdeid.Document) -> bool:

        patient = doc.metadata["patient"]

        if (patient is None) or (patient.surname is None):
            return False

        doc.metadata["surname_pattern"] = self._tokenizer.tokenize(patient.surname)

        return True

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        surname_pattern = metadata["surname_pattern"]
        surname_token = surname_pattern[0]
        start_token = token

        while True:

            if not str_match(surname_token.text, token.text, max_edit_distance=1):
                return

            match_end_token = token

            surname_token = surname_token.next()
            token = token.next()

            if surname_token is None:
                break  # end of pattern

            if token is None:
                return  # end of tokens

        return start_token, match_end_token


class PersonInitialsPattern(TokenPattern):
    def doc_precondition(self, doc: docdeid.Document) -> bool:

        patient = doc.get_metadata_item("patient")
        return (patient is not None) and (patient.initials is not None)

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if str_match(token.text, metadata["patient"].initials):
            return token, token

        return None


class PersonGivenNamePattern(TokenPattern):
    def doc_precondition(self, doc: docdeid.Document) -> bool:

        patient = doc.get_metadata_item("patient")
        return (patient is not None) and (patient.given_name is not None)

    def match(
        self, token: docdeid.Token, metadata: Optional[dict] = None
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if str_match(token.text, metadata["patient"].given_name) or (
            len(token) > 3 and str_match(token.text, metadata["patient"].given_name, max_edit_distance=1)
        ):

            return token, token

        return None
