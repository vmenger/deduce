from abc import ABC, abstractmethod
from typing import Union

import docdeid

from deduce import utility


class AnnotationContextPattern(ABC):
    def precondition(
        self, start_token: docdeid.Token, end_token: docdeid.Token
    ) -> bool:
        return True

    @abstractmethod
    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> bool:
        pass

    @abstractmethod
    def annotate(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> tuple:
        pass

    def apply(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> Union[None, tuple]:

        if not self.precondition(start_token, end_token):
            return None

        match = self.match(start_token, end_token, tag)

        if match:
            return self.annotate(start_token, end_token, tag)


class AnnotationContextPatternWithLookupList(AnnotationContextPattern, ABC):
    def __init__(self, lookup_lists, *args, **kwargs):
        self._lookup_lists = lookup_lists
        super().__init__(*args, **kwargs)


class InterfixContextPattern(AnnotationContextPatternWithLookupList):
    def precondition(
        self, start_token: docdeid.Token, end_token: docdeid.Token
    ) -> bool:

        return (
            end_token.next() is not None and
            end_token.next(2) is not None
        )

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> bool:

        return (
            utility.any_in_text(["initia", "naam"], tag) and
            end_token.next().text in self._lookup_lists["interfixes"] and
            end_token.next(2).text[0].isupper()
        )

    def annotate(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> tuple:

        return (
            start_token,
            end_token.next(2),
            f"{tag}+interfix+achternaam",
        )


class InitialsContextPattern(AnnotationContextPatternWithLookupList):
    def precondition(
        self, start_token: docdeid.Token, end_token: docdeid.Token
    ) -> bool:

        return start_token.previous() is not None

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> bool:

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

        return (
            utility.any_in_text(["achternaam", "interfix", "initia"], tag) and (
                previous_token_is_initial or
                previous_token_is_name
            )
        )

    def annotate(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> tuple:

        return start_token.previous(), end_token, f"initiaal+{tag}"


class InitialNameContextPattern(AnnotationContextPatternWithLookupList):
    def precondition(
        self, start_token: docdeid.Token, end_token: docdeid.Token
    ) -> bool:

        return end_token.next() is not None

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> bool:

        return (
            utility.any_in_text(["initia", "voornaam", "roepnaam", "prefix"], tag) and
            len(end_token.next().text) > 3 and
            end_token.next().text[0].isupper() and
            end_token.next().text.lower() not in self._lookup_lists["whitelist"]
        )

    def annotate(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> tuple:

        return (
            start_token,
            end_token.next(),
            f"{tag}+initiaalhoofdletternaam",
        )


class NexusContextPattern(AnnotationContextPattern):
    def precondition(
        self, start_token: docdeid.Token, end_token: docdeid.Token
    ) -> bool:

        return (
            end_token.next() is not None and
            end_token.next(2) is not None
        )

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> bool:

        return (
            end_token.next().text == "en" and
            end_token.next(2).text[0].isupper()
        )

    def annotate(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> tuple:

        return (
            start_token,
            end_token.next(2),
            f"{tag}+en+hoofdletternaam",
        )
