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

        return all([end_token.next() is not None, end_token.next(2) is not None])

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> bool:

        return all(
            [
                utility.any_in_text(["initia", "naam"], tag),
                end_token.next().text in self._lookup_lists["interfixes"],
                end_token.next(2).text[0].isupper(),
            ]
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

        previous_token_is_initial = all(
            [
                len(start_token.previous().text) == 1,
                start_token.previous().text[0].isupper(),
            ]
        )

        previous_token_is_name = all(
            [
                start_token.previous().text != "",
                start_token.previous().text[0].isupper(),
                start_token.previous().text.lower()
                not in self._lookup_lists["whitelist"],
                start_token.previous().text.lower()
                not in self._lookup_lists["prefixes"],
            ]
        )

        return all(
            [
                utility.any_in_text(["achternaam", "interfix", "initia"], tag),
                any([previous_token_is_initial, previous_token_is_name]),
            ]
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

        return all(
            [
                utility.any_in_text(["initia", "voornaam", "roepnaam", "prefix"], tag),
                len(end_token.next().text) > 3,
                end_token.next().text[0].isupper(),
                end_token.next().text.lower() not in self._lookup_lists["whitelist"],
            ]
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

        return all([end_token.next() is not None, end_token.next(2) is not None])

    def match(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> bool:

        return all(
            [
                end_token.next().text == "en",
                end_token.next(2).text[0].isupper(),
            ]
        )

    def annotate(
        self, start_token: docdeid.Token, end_token: docdeid.Token, tag: str
    ) -> tuple:

        return (
            start_token,
            end_token.next(2),
            f"{tag}+en+hoofdletternaam",
        )
