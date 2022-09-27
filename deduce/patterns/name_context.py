from abc import ABC, abstractmethod
from typing import Union, Optional

import docdeid

from deduce import utility


class AnnotationContextPattern(ABC):

    def __init__(self, tag: str):
        self.tag = tag

    def document_precondition(self, doc: docdeid.Document) -> bool:
        """ Use this to check if the pattern is applicable to the document. """
        return True

    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:
        """ Use this to check if the pattern is applicable to the token. """
        return True

    @abstractmethod
    def match(self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str) -> Optional[tuple[docdeid.Token, docdeid.Token]]:
        pass


class AnnotationContextPatternWithLookupList(AnnotationContextPattern, ABC):
    def __init__(self, lookup_lists, *args, **kwargs):
        self._lookup_lists = lookup_lists
        super().__init__(*args, **kwargs)


class InterfixContextPattern(AnnotationContextPatternWithLookupList):

    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return (
            end_token.next() is not None and
            end_token.next(2) is not None
        )

    def match(self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            utility.any_in_text(["initia", "naam"], tag) and
            end_token.next().text in self._lookup_lists["interfixes"] and
            end_token.next(2).text[0].isupper()
        ):

            return start_token, end_token.next(2)


class InitialsContextPattern(AnnotationContextPatternWithLookupList):

    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return start_token.previous() is not None

    def match(self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        previous_token_is_initial = (
            len(start_token.previous().text) == 1 and
            start_token.previous().text[0].isupper()
        )

        previous_token_is_name = (
            start_token.previous().text != "" and
            start_token.previous().text[0].isupper() and
            start_token.previous().text.lower() not in self._lookup_lists["whitelist"] and
            start_token.previous().text.lower() not in self._lookup_lists["prefixes"]
        )

        if (
            utility.any_in_text(["achternaam", "interfix", "initia"], tag) and (
                previous_token_is_initial or
                previous_token_is_name
            )
        ):

            return start_token.previous(), end_token


class InitialNameContextPattern(AnnotationContextPatternWithLookupList):

    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return end_token.next() is not None

    def match(self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            utility.any_in_text(["initia", "voornaam", "roepnaam", "prefix"], tag) and
            len(end_token.next().text) > 3 and
            end_token.next().text[0].isupper() and
            end_token.next().text.lower() not in self._lookup_lists["whitelist"]
        ):

            return start_token, end_token.next()


class NexusContextPattern(AnnotationContextPattern):

    def token_precondition(self, start_token: docdeid.Token, end_token: docdeid.Token) -> bool:

        return (
            end_token.next() is not None and
            end_token.next(2) is not None
        )

    def match(self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str) -> Optional[tuple[docdeid.Token, docdeid.Token]]:

        if (
            end_token.next().text == "en" and
            end_token.next(2).text[0].isupper()
        ):

            return start_token, end_token.next(2)
