from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import docdeid
from nltk import edit_distance


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

        return all(
            [
                token.text.lower() in self._lookup_lists["prefixes"],
                token.next().text[0].isupper(),
                token.next().text.lower() not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token.next(), self._tag


class InterfixWithNamePattern(TokenPatternWithLookup):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:
        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token.text.lower() in self._lookup_lists["interfixes"],
                token.next().text in self._lookup_lists["interfix_surnames"],
                token.next().text.lower() not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token.next(), self._tag


class InitialWithCapitalPattern(TokenPatternWithLookup):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return token.next() is not None

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token.text[0].isupper(),
                len(token.text) == 1,
                len(token.next().text) > 3,
                token.next().text[0].isupper(),
                token.next().text.lower() not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token.next(), self._tag


class InitiaalInterfixCapitalPattern(TokenPatternWithLookup):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                token.previous() is not None,
                token.next() is not None,
            ]
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token.previous().text[0].isupper(),
                len(token.previous().text) == 1,
                token.text in self._lookup_lists["interfixes"],
                token.next().text[0].isupper(),
            ]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token.previous(), token.next(), self._tag


class FirstNameLookupPattern(TokenPatternWithLookup):
    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token.text in self._lookup_lists["first_names"],
                token.text.lower() not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token, self._tag


class SurnameLookupPattern(TokenPatternWithLookup):
    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:
        return all(
            [
                token.text in self._lookup_lists["surnames"],
                token.text.lower() not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:
        return token, token, self._tag


class PersonFirstNamePattern(TokenPattern):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].first_names is not None,
            ]
        )

    def match(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data["person"].first_names):

            condition = token.text == first_name or all(
                [
                    len(token.text) > 3,
                    edit_distance(token.text, first_name, transpositions=True) <= 1,
                ]
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

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].first_names is not None,
            ]
        )

    def match(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data["person"].first_names):

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

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].surname is not None,
            ]
        )

    def match(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        surname_pattern = self._tokenizer.tokenize(meta_data["patient_surname"])
        surname_token = surname_pattern[0]

        while True:

            if (
                not edit_distance(surname_token.text, token.text, transpositions=True)
                <= 1
            ):
                return False

            match_end_token = token

            surname_token = surname_token.next()
            token = token.next()

            if token is None:
                return False

            if surname_token is None:
                break

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

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].initials is not None,
            ]
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return token.text == meta_data["person"].initials

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token, self._tag


class PersonGivenNamePattern(TokenPattern):
    def precondition(
        self, token: docdeid.Token, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].given_name is not None,
            ]
        )

    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> bool:

        return (token.text == meta_data["person"].given_name) or all(
            [
                len(token.text) > 3,
                edit_distance(
                    token.text,
                    meta_data["person"].given_name,
                    transpositions=True,
                )
                <= 1,
            ]
        )

    def annotate(self, token: docdeid.Token, match_info=None) -> tuple:

        return token, token, self._tag
