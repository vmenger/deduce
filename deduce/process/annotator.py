import re
from typing import Optional

import docdeid as dd
from docdeid import Annotation, Document

import deduce.utils
from deduce.pattern.name_context import AnnotationContextPattern


class AnnotationContextPatternAnnotator(dd.process.Annotator):
    """
    This Annotator applies one or more AnnotationContextPattern to the text. Currently, it applies all patterns to an
    existing annotation sequentially, and moves to the next annotation when a pattern matches. Therefore, if multiple
    patterns match an annotation, only the first one is applied. This may change in future versions. It's important that
    this annotator goes beyond the relevant annotators, so that the AnnotationContextPatterns are applied to the
    relevant annotations.

    Arguments:
        context_patterns: The patterns to apply.
        tags: A list of tags that can be used to filter the existing annotations. Patterns will only be applied to
            those annotations that have one of the tags as substring of the annotation tag.
        iterative: Whether to repeatedly apply the pattenrs until no changes occur.
    """

    def __init__(
        self, context_patterns: list[AnnotationContextPattern], tags: Optional[list[str]] = None, iterative: bool = True
    ) -> None:
        self._context_patterns = context_patterns
        self._tags = tags
        self._iterative = iterative
        super().__init__(tag="_")

    def get_matching_tag_annotations(self, context_annotations: list[dd.Annotation]) -> list[dd.Annotation]:
        """
        Filter the existing annotations based on their tags.

        Args:
            context_annotations: The existing annotations.

        Returns:
            The annotations that match according to the ``_tags`` property.
        """

        if self._tags is not None:

            context_annotations = [
                annotation for annotation in context_annotations if deduce.utils.any_in_text(self._tags, annotation.tag)
            ]

        return context_annotations

    def _annotate_context(self, annotations: list[dd.Annotation], doc: dd.Document) -> list[dd.Annotation]:
        """
        Apply the context patterns.

        Args:
            annotations: The existing annotations.
            doc: The document.

        Returns:
            The modified annotations, after the patterns are applied to them.
        """

        context_patterns = [pattern for pattern in self._context_patterns if pattern.document_precondition(doc)]

        next_annotations = []

        for annotation in annotations:

            changes = False

            for context_pattern in context_patterns:

                if not context_pattern.annotation_precondition(annotation):

                    continue

                match = context_pattern.match(annotation)

                if match is None:
                    continue

                start_token, end_token = match

                next_annotations.append(
                    dd.Annotation(
                        text=doc.text[start_token.start_char : end_token.end_char],
                        start_char=start_token.start_char,
                        end_char=end_token.end_char,
                        tag=context_pattern.tag.format(tag=annotation.tag),
                        start_token=start_token,
                        end_token=end_token,
                    )
                )

                changes = True
                break

            if changes:
                continue

            next_annotations.append(annotation)

        # changes
        if self._iterative and (set(annotations) != set(next_annotations)):
            next_annotations = self._annotate_context(next_annotations, doc)

        return next_annotations

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:
        context_annotations = self.get_matching_tag_annotations(list(doc.annotations))
        doc.annotations.difference_update(context_annotations)

        return self._annotate_context(context_annotations, doc)


class BsnAnnotator(dd.process.Annotator):
    """Annotates BSN nummers."""

    @staticmethod
    def _elfproef(bsn: str) -> bool:

        if len(bsn) != 9 or (any(not char.isdigit() for char in bsn)):
            raise ValueError("Elfproef for testing BSN can only be applied to strings with 9 digits.")

        total = 0

        for char, factor in zip(bsn, [9, 8, 7, 6, 5, 4, 3, 2, -1]):
            total += int(char) * factor

        return total % 11 == 0

    def annotate(self, doc: Document) -> list[Annotation]:

        bsn_regexp = re.compile(r"(\D|^)(\d{9})(\D|$)")
        capt_group = 2

        annotations = []

        for match in bsn_regexp.finditer(doc.text):

            text = match.group(capt_group)
            start, end = match.span(capt_group)

            if self._elfproef(text):
                annotations.append(Annotation(text=text, start_char=start, end_char=end, tag=self.tag))

        return annotations


class PhoneNumberAnnotator(dd.process.Annotator):
    """Annotates phone numbers."""

    def __init__(self, phone_regexp: str, *args, min_digits: int = 9, max_digits: int = 11, **kwargs) -> None:

        self.phone_regexp = re.compile(phone_regexp)
        self.min_digits = min_digits
        self.max_digits = max_digits

        super().__init__(*args, **kwargs)

    def annotate(self, doc: Document) -> list[Annotation]:

        annotations = []

        for match in self.phone_regexp.finditer(doc.text):

            digit_len_shift = 0
            left_index_shift = 0
            prefix_with_parens = match.group(2)
            prefix_digits = "0" + re.sub(r"\D", "", match.group(4))
            number_digits = re.sub(r"\D", "", match.group(5))

            # Trim parenthesis
            if prefix_with_parens.startswith("(") and not prefix_with_parens.endswith(")"):
                left_index_shift = 1

            # Check max 1 hyphen
            if len(re.findall("-", match.group(0))) > 1:
                continue

            # Shift num digits for shorter numbers
            if prefix_digits in ["0800", "0900", "0906", "0909"]:
                digit_len_shift = -2

            if (
                (self.min_digits + digit_len_shift)
                <= (len(prefix_digits) + len(number_digits))
                <= (self.max_digits + digit_len_shift)
            ):
                text = match.group(0)[left_index_shift:]
                start_char, end_char = match.span(0)
                start_char += left_index_shift

                annotations.append(Annotation(text=text, start_char=start_char, end_char=end_char, tag=self.tag))

        return annotations
