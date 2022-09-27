from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import docdeid
from rapidfuzz.distance import DamerauLevenshtein


class TokenPattern(ABC):
    def __init__(self, tag: str):
        self.tag = tag

    def document_precondition(self, doc: docdeid.Document) -> bool:
        """ Use this to check if the pattern is applicable to the document. """
        return True

    def token_precondition(self, token: docdeid.Token) -> bool:
        """ Use this to check if the pattern is applicable to the token. """
        return True

    @abstractmethod
    def match(self, token: docdeid.Token, meta_data: Optional[dict] = None) -> Optional[tuple[docdeid.Token, docdeid.Token]]:
        """ Check if the pattern matches the token. """
        pass


class TokenPatternWithLookup(TokenPattern, ABC):
    def __init__(self, lookup_lists, *args, **kwargs):
        self._lookup_lists = lookup_lists
        super().__init__(*args, **kwargs)


class TokenPatternAnnotator(docdeid.BaseAnnotator):

    def __init__(self, pattern: TokenPattern):
        self.pattern = pattern

    def annotate(self, doc: docdeid.Document):

        if not self.pattern.document_precondition(doc):
            return

        for i, token in enumerate(doc.tokens):

            if not self.pattern.token_precondition(token):
                continue

            match = self.pattern.match(token, doc.get_meta_data())

            if match is None:
                continue

            start_token, end_token = match

            doc.add_annotation(
                docdeid.Annotation(
                    text=doc.text[start_token.start_char : end_token.end_char],
                    start_char=start_token.start_char,
                    end_char=end_token.end_char,
                    tag=self.pattern.tag,
                    start_token=start_token,
                    end_token=end_token
                )
            )


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
            len(token.text) == 1 and
            len(token.next().text) > 3 and
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
            len(token.previous().text) == 1 and
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
                    token.text == first_name or (
                            len(token.text) > 3 and
                            DamerauLevenshtein.distance(token.text, first_name, score_cutoff=1) <= 1
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

            if token.text == first_name[0]:

                next_token = token.next()

                if (next_token is not None) and next_token == ".":
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

            if DamerauLevenshtein.distance(surname_token.text, token.text, score_cutoff=1) > 1:
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

        if token.text == meta_data["patient"].initials:
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
            token.text == meta_data["patient"].given_name or (
                len(token.text) > 3 and
                DamerauLevenshtein.distance(token.text, meta_data["patient"].given_name, score_cutoff=1) <= 1
            )
        ):

            return token, token
