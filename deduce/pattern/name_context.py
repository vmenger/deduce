from abc import ABC, abstractmethod
from typing import Optional

import docdeid as dd

from deduce import utils


class AnnotationContextPattern(ABC):
    def __init__(self, tag: str) -> None:
        self.tag = tag

    def document_precondition(self, doc: dd.Document) -> bool:
        """Use this to check if the pattern is applicable to the document."""
        return True

    def annotation_precondition(self, annotation: dd.Annotation) -> bool:
        """Use this to check if the pattern is applicable to the annotation."""
        return True

    @abstractmethod
    def match(self, annotation: dd.Annotation) -> Optional[tuple[dd.Token, dd.Token]]:
        pass


class AnnotationContextPatternWithLookupSet(AnnotationContextPattern, ABC):
    def __init__(self, lookup_sets: dd.ds.DsCollection[dd.LookupSet], *args, **kwargs) -> None:
        self._lookup_sets = lookup_sets
        super().__init__(*args, **kwargs)


class InterfixContextPattern(AnnotationContextPatternWithLookupSet):
    def annotation_precondition(self, annotation: dd.Annotation) -> bool:

        return annotation.end_token.next() is not None and annotation.end_token.next(2) is not None

    def match(self, annotation: dd.Annotation) -> Optional[tuple[dd.Token, dd.Token]]:

        if (
            utils.any_in_text(["initia", "naam"], annotation.tag)
            and annotation.end_token.next().text in self._lookup_sets["interfixes"]
            and annotation.end_token.next(2).text[0].isupper()
        ):

            return annotation.start_token, annotation.end_token.next(2)

        return None


class InitialsContextPattern(AnnotationContextPatternWithLookupSet):
    def annotation_precondition(self, annotation: dd.Annotation) -> bool:

        return annotation.start_token.previous() is not None

    def match(self, annotation: dd.Annotation) -> Optional[tuple[dd.Token, dd.Token]]:

        previous_token_is_initial = (
            len(annotation.start_token.previous().text) == 1 and annotation.start_token.previous().text[0].isupper()
        )

        previous_token_is_name = (
            annotation.start_token.previous().text != ""
            and annotation.start_token.previous().text[0].isupper()
            and annotation.start_token.previous().text not in self._lookup_sets["whitelist"]
            and annotation.start_token.previous().text.lower() not in self._lookup_sets["prefixes"]
        )

        if utils.any_in_text(["achternaam", "interfix", "initia"], annotation.tag) and (
            previous_token_is_initial or previous_token_is_name
        ):

            return annotation.start_token.previous(), annotation.end_token

        return None


class InitialNameContextPattern(AnnotationContextPatternWithLookupSet):
    def annotation_precondition(self, annotation: dd.Annotation) -> bool:

        return annotation.end_token.next() is not None

    def match(self, annotation: dd.Annotation) -> Optional[tuple[dd.Token, dd.Token]]:

        if (
            utils.any_in_text(["initia", "voornaam", "roepnaam", "prefix"], annotation.tag)
            and len(annotation.end_token.next().text) > 3
            and annotation.end_token.next().text[0].isupper()
            and annotation.end_token.next().text not in self._lookup_sets["whitelist"]
        ):

            return annotation.start_token, annotation.end_token.next()

        return None


class NexusContextPattern(AnnotationContextPattern):
    def annotation_precondition(self, annotation: dd.Annotation) -> bool:

        return annotation.end_token.next() is not None and annotation.end_token.next(2) is not None

    def match(self, annotation: dd.Annotation) -> Optional[tuple[dd.Token, dd.Token]]:

        if annotation.end_token.next().text == "en" and annotation.end_token.next(2).text[0].isupper():

            return annotation.start_token, annotation.end_token.next(2)

        return None
