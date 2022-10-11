from abc import ABC, abstractmethod
from typing import Optional

import docdeid

from deduce import utils


class AnnotationContextPattern(ABC):
    def __init__(self, tag: str) -> None:
        self.tag = tag

    def document_precondition(self, doc: docdeid.Document) -> bool:
        """Use this to check if the pattern is applicable to the document."""
        return True

    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:
        """Use this to check if the pattern is applicable to the token."""
        return True

    @abstractmethod
    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:
        pass


class AnnotationContextPatternWithLookupSet(AnnotationContextPattern, ABC):
    def __init__(self, lookup_sets: docdeid.DsCollection, *args, **kwargs) -> None:
        self._lookup_sets = lookup_sets
        super().__init__(*args, **kwargs)


class InterfixContextPattern(AnnotationContextPatternWithLookupSet):
    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return end_token.next() is not None and end_token.next(2) is not None

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            utils.any_in_text(["initia", "naam"], tag)
            and end_token.next().text in self._lookup_sets["interfixes"]
            and end_token.next(2).text[0].isupper()
        ):

            return start_token, end_token.next(2)

        return None


class InitialsContextPattern(AnnotationContextPatternWithLookupSet):
    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return start_token.previous() is not None

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        previous_token_is_initial = len(start_token.previous().text) == 1 and start_token.previous().text[0].isupper()

        previous_token_is_name = (
            start_token.previous().text != ""
            and start_token.previous().text[0].isupper()
            and start_token.previous().text not in self._lookup_sets["whitelist"]
            and start_token.previous().text.lower() not in self._lookup_sets["prefixes"]
        )

        if utils.any_in_text(["achternaam", "interfix", "initia"], tag) and (
            previous_token_is_initial or previous_token_is_name
        ):

            return start_token.previous(), end_token

        return None


class InitialNameContextPattern(AnnotationContextPatternWithLookupSet):
    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return end_token.next() is not None

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            utils.any_in_text(["initia", "voornaam", "roepnaam", "prefix"], tag)
            and len(end_token.next().text) > 3
            and end_token.next().text[0].isupper()
            and end_token.next().text not in self._lookup_sets["whitelist"]
        ):

            return start_token, end_token.next()

        return None


class NexusContextPattern(AnnotationContextPattern):
    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return end_token.next() is not None and end_token.next(2) is not None

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if end_token.next().text == "en" and end_token.next(2).text[0].isupper():

            return start_token, end_token.next(2)

        return None
