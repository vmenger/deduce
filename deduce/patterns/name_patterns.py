import itertools
from typing import Any, Optional, Union

from nltk import edit_distance

from deduce.tokenizer import TokenContext, TokenContextPattern


class TokenContextPatternWithLookup(TokenContextPattern):
    def __init__(self, lookup_lists, *args, **kwargs):
        self._lookup_lists = lookup_lists
        super().__init__(*args, **kwargs)


class PrefixWithNamePattern(TokenContextPatternWithLookup):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return token_context.next_token is not None

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                token_context.token.text.lower() in self._lookup_lists["prefixes"],
                token_context.next_token.text[0].isupper(),
                token_context.next_token.text.lower()
                not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.next_token, self._tag


class InterfixWithNamePattern(TokenContextPatternWithLookup):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:
        return token_context.next_token is not None

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                token_context.token.text.lower() in self._lookup_lists["interfixes"],
                token_context.next_token.text
                in self._lookup_lists["interfix_surnames"],
                token_context.next_token.text.lower()
                not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.next_token, self._tag


class InitialWithCapitalPattern(TokenContextPatternWithLookup):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return token_context.next_token is not None

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                token_context.token.text[0].isupper(),
                len(token_context.token.text) == 1,
                len(token_context.next_token.text) > 3,
                token_context.next_token.text[0].isupper(),
                token_context.next_token.text.lower()
                not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.next_token, self._tag


class InitiaalInterfixCapitalPattern(TokenContextPatternWithLookup):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                token_context.previous_token is not None,
                token_context.next_token is not None,
            ]
        )

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                token_context.previous_token.text[0].isupper(),
                len(token_context.previous_token.text) == 1,
                token_context.token.text in self._lookup_lists["interfixes"],
                token_context.next_token.text[0].isupper(),
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.previous_token, token_context.next_token, self._tag


class FirstNameLookupPattern(TokenContextPatternWithLookup):
    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                token_context.token.text in self._lookup_lists["first_names"],
                token_context.token.text.lower() not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.token, self._tag


class SurnameLookupPattern(TokenContextPatternWithLookup):
    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:
        return all(
            [
                token_context.token.text in self._lookup_lists["surnames"],
                token_context.token.text.lower() not in self._lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:
        return token_context.token, token_context.token, self._tag


class PersonFirstNamePattern(TokenContextPattern):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].first_names is not None,
            ]
        )

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data["person"].first_names):

            condition = token_context.token.text == first_name or all(
                [
                    len(token_context.token.text) > 3,
                    edit_distance(
                        token_context.token.text, first_name, transpositions=True
                    )
                    <= 1,
                ]
            )

            if condition:
                return True, token_context.token.index

        return False

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return (
            token_context.get_token(pos=match_info),
            token_context.get_token(pos=match_info),
            self._tag,
        )


class PersonInitialFromNamePattern(TokenContextPattern):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].first_names is not None,
            ]
        )

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data["person"].first_names):

            if token_context.token.text == first_name[0]:

                next_token = token_context.next(1)
                if (next_token is not None) and next_token == ".":
                    return True, (token_context.token.index, next_token.index)

                return True, (token_context.token.index, token_context.token.index)

        return False

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return (
            token_context.get_token(pos=match_info[0]),
            token_context.get_token(pos=match_info[1]),
            self._tag,
        )


class PersonSurnamePattern(TokenContextPattern):
    def __init__(self, tokenizer, *args, **kwargs):
        self._tokenizer = tokenizer
        super().__init__(*args, **kwargs)

    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].surname is not None,
            ]
        )

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:

        surname_pattern = [
            token.text
            for token in self._tokenizer.tokenize(meta_data["patient_surname"])
        ]

        if len(surname_pattern) > token_context.num_tokens_from_position():
            return False

        return (
            all(
                [
                    edit_distance(
                        surname_token,
                        token_context.get_token_at_num_from_position(i).text,
                        transpositions=True,
                    )
                    <= 1
                    for surname_token, i in zip(surname_pattern, itertools.count())
                ]
            ),
            len(surname_pattern) - 1,
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return (
            token_context.get_token_at_num_from_position(0),
            token_context.get_token_at_num_from_position(match_info),
            self._tag,
        )


class PersonInitialsPattern(TokenContextPattern):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].initials is not None,
            ]
        )

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return token_context.token.text == meta_data["person"].initials

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.token, self._tag


class PersonGivenNamePattern(TokenContextPattern):
    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return all(
            [
                meta_data is not None,
                "person" in meta_data,
                meta_data["person"].given_name is not None,
            ]
        )

    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:

        return (token_context.token.text == meta_data["person"].given_name) or all(
            [
                len(token_context.token.text) > 3,
                edit_distance(
                    token_context.token.text,
                    meta_data["person"].given_name,
                    transpositions=True,
                )
                <= 1,
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.token, self._tag
