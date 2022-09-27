from abc import ABC
from typing import Optional, Union

import docdeid
from docdeid.pattern.pattern import TokenPattern
from rapidfuzz.distance import DamerauLevenshtein


def str_match(s1: Union[docdeid.Token, str], s2: Union[docdeid.Token, str], max_edit_distance: Optional[int] = None):

    if isinstance(s1, docdeid.Token):
        s1 = s1.text

    if isinstance(s2, docdeid.Token):
        s2 = s2.text

    if max_edit_distance is not None:
        return DamerauLevenshtein.distance(s1, s2, score_cutoff=max_edit_distance) <= max_edit_distance

    return s1 == s2


class TokenPatternWithLookup(TokenPattern, ABC):
    def __init__(self, lookup_lists, *args, **kwargs):
        self._lookup_lists = lookup_lists
        super().__init__(*args, **kwargs)


class PrefixWithNamePattern(TokenPatternWithLookup):

    def token_precondition(self, token: docdeid.Token) -> bool:

        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.text.lower() in self._lookup_lists["prefixes"] and
            token.next().text[0].isupper() and
            token.next().text.lower() not in self._lookup_lists["whitelist"]
        ):

            return token, token.next()


class InterfixWithNamePattern(TokenPatternWithLookup):

    def token_precondition(self, token: docdeid.Token) -> bool:

        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.text.lower() in self._lookup_lists["interfixes"] and
            token.next().text in self._lookup_lists["interfix_surnames"] and
            token.next().text.lower() not in self._lookup_lists["whitelist"]
        ):

            return token, token.next()


class InitialWithCapitalPattern(TokenPatternWithLookup):

    def token_precondition(self, token: docdeid.Token) -> bool:

        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.text[0].isupper() and
            len(token) == 1 and
            len(token.next()) > 3 and
            token.next().text[0].isupper() and
            token.next().text.lower() not in self._lookup_lists["whitelist"]
        ):

            return token, token.next()


class InitiaalInterfixCapitalPattern(TokenPatternWithLookup):

    def token_precondition(self, token: docdeid.Token) -> bool:

        return (
            (token.previous() is not None) and
            (token.next() is not None)
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.previous().text[0].isupper() and
            len(token.previous()) == 1 and
            token.text in self._lookup_lists["interfixes"] and
            token.next().text[0].isupper()
        ):

            return token.previous(), token.next()


class FirstNameLookupPattern(TokenPatternWithLookup):
    # TODO: make this a separate annotator class

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.text in self._lookup_lists["first_names"] and
            token.text.lower() not in self._lookup_lists["whitelist"]
        ):

            return token, token


class SurnameLookupPattern(TokenPatternWithLookup):
    # TODO: make this a separate annotator class

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            token.text in self._lookup_lists["surnames"] and
            token.text.lower() not in self._lookup_lists["whitelist"]
        ):

            return token, token


class PersonFirstNamePattern(TokenPattern):

    def document_precondition(self, doc: docdeid.Document) -> bool:

        meta_data = doc.get_meta_data()

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data['patient'].first_names is not None)
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        for i, first_name in enumerate(meta_data["patient"].first_names):

            if (
                    str_match(token, first_name) or (
                            len(token.text) > 3 and
                            str_match(token, first_name, max_edit_distance=1)
                    )
            ):

                return token, token


class PersonInitialFromNamePattern(TokenPattern):

    def document_precondition(self, doc: docdeid.Document) -> bool:

        meta_data = doc.get_meta_data()

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data["patient"].first_names is not None)
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        for i, first_name in enumerate(meta_data["patient"].first_names):

            if str_match(token, first_name[0]):

                next_token = token.next()

                if (next_token is not None) and str_match(next_token, "."):
                    return token, next_token

                return token, token


class PersonSurnamePattern(TokenPattern):

    def __init__(self, tokenizer, *args, **kwargs):
        self._tokenizer = tokenizer
        super().__init__(*args, **kwargs)

    def document_precondition(self, doc: docdeid.Document) -> bool:

        meta_data = doc.get_meta_data()

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data["patient"].surname is not None)
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        surname_pattern = self._tokenizer.tokenize(meta_data["patient"].surname)  # todo: tokenize once
        surname_token = surname_pattern[0]
        start_token = token

        while True:

            if not str_match(surname_token, token, max_edit_distance=1):
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

    def document_precondition(self, doc: docdeid.Document) -> bool:

        meta_data = doc.get_meta_data()

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data["patient"].initials is not None)
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if str_match(token, meta_data["patient"].initials):
            return token, token


class PersonGivenNamePattern(TokenPattern):

    def document_precondition(self, doc: docdeid.Document) -> bool:

        meta_data = doc.get_meta_data()

        return (
            meta_data is not None and
            "patient" in meta_data and
            meta_data["patient"].given_name is not None
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            str_match(token, meta_data["patient"].given_name) or (
                len(token) > 3 and
                str_match(token, meta_data["patient"].given_name, max_edit_distance=1)
            )
        ):

            return token, token
