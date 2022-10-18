""" The annotate module contains the code for annotating text"""
from typing import Optional

import docdeid as dd

import deduce.utils
from deduce.pattern.name_context import AnnotationContextPattern


class AnnotationContextPatternAnnotator(dd.annotate.BaseAnnotator):
    """This needs to go after the relevant annotators."""

    def __init__(
        self, context_patterns: list[AnnotationContextPattern], tags: Optional[list[str]] = None, iterative: bool = True
    ) -> None:
        self._context_patterns = context_patterns
        self._tags = tags
        self._iterative = iterative
        super().__init__(tag=None)

    def get_matching_tag_annotations(self, context_annotations: dd.AnnotationSet) -> dd.AnnotationSet:

        if self._tags is not None:

            context_annotations = [
                annotation for annotation in context_annotations if deduce.utils.any_in_text(self._tags, annotation.tag)
            ]

        return dd.AnnotationSet(context_annotations)

    def _annotate_context(self, annotations: dd.AnnotationSet, doc: dd.Document) -> list[dd.Annotation]:

        context_patterns = [pattern for pattern in self._context_patterns if pattern.document_precondition(doc)]

        next_annotations = dd.AnnotationSet()

        for annotation in annotations:

            changes = False

            for context_pattern in context_patterns:

                if not context_pattern.annotation_precondition(annotation):

                    continue

                match = context_pattern.match(annotation)

                if match is None:
                    continue

                start_token, end_token = match

                next_annotations.add(
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

            next_annotations.add(annotation)

        # changes
        if self._iterative and (annotations != next_annotations):
            next_annotations = self._annotate_context(next_annotations, doc)

        return next_annotations

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:

        context_annotations = self.get_matching_tag_annotations(doc.annotations)
        doc.annotations.difference_update(context_annotations)

        return self._annotate_context(context_annotations, doc)
