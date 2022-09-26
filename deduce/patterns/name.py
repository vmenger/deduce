from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import docdeid
from rapidfuzz.distance import DamerauLevenshtein



class TokenPattern(ABC):
    def __init__(self, tag: str):
        self._tag = tag

    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:
        return True

    @abstractmethod
    def match(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:
        pass

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:
        return token, token, self._tag

    def apply(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[None, tuple]:

        if not self.precondition(token, meta_data):
            return None

        match = self.match(token, meta_data)
        match_info = None

        if isinstance(match, tuple):
            match, match_info = match  # unpack

        if match:
            return self.annotate(token, match_info)


class TokenPatternWithLookup(TokenPattern, ABC):
    def __init__(self, lookup_lists, *args, **kwargs):
        self._lookup_lists = lookup_lists
        super().__init__(*args, **kwargs)


class PrefixWithNamePattern(TokenPatternWithLookup):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (
            token.text.lower() in self._lookup_lists["prefixes"] and
            token.next().text[0].isupper() and
            token.next().text.lower() not in self._lookup_lists["whitelist"]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token.next(), self._tag


class InterfixWithNamePattern(TokenPatternWithLookup):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (
            token.text.lower() in self._lookup_lists["interfixes"] and
            token.next().text in self._lookup_lists["interfix_surnames"] and
            token.next().text.lower() not in self._lookup_lists["whitelist"]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token.next(), self._tag


class InitialWithCapitalPattern(TokenPatternWithLookup):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (
            token.text[0].isupper() and
            len(token.text) == 1 and
            len(token.next().text) > 3 and
            token.next().text[0].isupper() and
            token.next().text.lower() not in self._lookup_lists["whitelist"]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token.next(), self._tag


class InitiaalInterfixCapitalPattern(TokenPatternWithLookup):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return (
            (token.previous() is not None) and
            (token.next() is not None)
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (
            token.previous().text[0].isupper() and
            len(token.previous().text) == 1 and
            token.text in self._lookup_lists["interfixes"] and
            token.next().text[0].isupper()
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token.previous(), token.next(), self._tag


class FirstNameLookupPattern(TokenPatternWithLookup):

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (
            token.text in self._lookup_lists["first_names"] and
            token.text.lower() not in self._lookup_lists["whitelist"]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token, self._tag


class SurnameLookupPattern(TokenPatternWithLookup):

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (
            token.text in self._lookup_lists["surnames"] and
            token.text.lower() not in self._lookup_lists["whitelist"]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:
        return token, token, self._tag


class PersonFirstNamePattern(TokenPattern):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data['patient'].first_names is not None)
        )

    def match(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data["patient"].first_names):

            condition = (
                    token.text == first_name or (
                            len(token.text) > 3 and
                            DamerauLevenshtein.distance(token.text, first_name, score_cutoff=1) <= 1
                    )
            )

            if condition:
                return True, token

        return False

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return (
            match_info,
            match_info,
            self._tag,
        )


class PersonInitialFromNamePattern(TokenPattern):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data["patient"].first_names is not None)
        )

    def match(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data["patient"].first_names):

            if token.text == first_name[0]:

                next_token = token.next()

                if (next_token is not None) and next_token == ".":
                    return True, (token, next_token)

                return True, (token, token)

        return False

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return (
            match_info[0],
            match_info[1],
            self._tag,
        )


class PersonSurnamePattern(TokenPattern):
    def __init__(self, tokenizer, *args, **kwargs):
        self._tokenizer = tokenizer
        super().__init__(*args, **kwargs)

    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data["patient"].surname is not None)
        )

    def match(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        surname_pattern = self._tokenizer.tokenize(meta_data["patient"].surname)
        surname_token = surname_pattern[0]

        while True:

            if (
                not DamerauLevenshtein.distance(surname_token.text, token.text, score_cutoff=1)
                <= 1
            ):
                return False

            match_end_token = token

            surname_token = surname_token.next()
            token = token.next()

            if surname_token is None:
                break

            if token is None:
                return False

        return True, match_end_token

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return (
            token,
            match_info,
            self._tag,
        )


class PersonInitialsPattern(TokenPattern):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return (
            (meta_data is not None) and
            ("patient" in meta_data) and
            (meta_data["patient"].initials is not None)
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return token.text == meta_data["patient"].initials

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token, self._tag


class PersonGivenNamePattern(TokenPattern):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return (
            meta_data is not None and
            "patient" in meta_data and
            meta_data["patient"].given_name is not None
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (
            token.text == meta_data["patient"].given_name or (
                len(token.text) > 3 and
                DamerauLevenshtein.distance(token.text, meta_data["patient"].given_name, score_cutoff=1) <= 1
            )
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token, self._tag
