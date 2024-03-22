"""Contains components for processing AnnotationSet."""

import docdeid as dd
from docdeid import AnnotationSet
from frozendict import frozendict


class DeduceMergeAdjacentAnnotations(dd.process.MergeAdjacentAnnotations):
    """Merge adjacent tags, according to deduce logic: adjacent annotations with mixed
    patient/person tags are replaced with a patient annotation, in other cases only
    annotations with equal tags are considered adjacent."""

    def _tags_match(self, left_tag: str, right_tag: str) -> bool:
        """
        Define whether two tags match. This is the case when they are equal strings, and
        additionally patient and person tags are also regarded as equal.

        Args:
            left_tag: The left tag.
            right_tag: The right tag.

        Returns:
            ``True`` if tags match, ``False`` otherwise.
        """

        return (left_tag == right_tag) or {left_tag, right_tag} == {
            "patient",
            "persoon",
        }

    def _adjacent_annotations_replacement(
        self,
        left_annotation: dd.Annotation,
        right_annotation: dd.Annotation,
        text: str,
    ) -> dd.Annotation:
        """
        Replace two annotations that have equal tags with a new annotation.

        If one of the two annotations has the patient tag, the new annotation will also
        be tagged patient. In other cases, the tags are already equal.
        """

        if left_annotation.tag != right_annotation.tag:
            replacement_tag = "patient"
        else:
            replacement_tag = left_annotation.tag

        return dd.Annotation(
            text=text[left_annotation.start_char : right_annotation.end_char],
            start_char=left_annotation.start_char,
            end_char=right_annotation.end_char,
            tag=replacement_tag,
        )


class PersonAnnotationConverter(dd.process.AnnotationProcessor):
    """
    Responsible for processing the annotations produced by all name annotators (regular
    and context-based).

    Any overlap with annotations that are  contain "pseudo" in their tag are removed, as
    are those annotations. Then resolves overlap between remaining annotations, and maps
    the tags to either "patient" or "persoon", based on whether "patient" is in the tag
    (e.g. voornaam_patient => patient, achternaam_onbekend => persoon).
    """

    def __init__(self) -> None:
        def map_tag_to_prio(tag: str) -> int:
            if "pseudo" in tag:
                return 0
            if "patient" in tag:
                return 1

            return 2

        self._overlap_resolver = dd.process.OverlapResolver(
            sort_by=("tag", "length"),
            sort_by_callbacks=frozendict(
                tag=map_tag_to_prio,
                length=lambda x: -x,
            ),
        )

    def process_annotations(
        self, annotations: dd.AnnotationSet, text: str
    ) -> dd.AnnotationSet:
        new_annotations = self._overlap_resolver.process_annotations(
            annotations, text=text
        )

        return dd.AnnotationSet(
            dd.Annotation(
                text=annotation.text,
                start_char=annotation.start_char,
                end_char=annotation.end_char,
                tag="patient" if "patient" in annotation.tag else "persoon",
                source=annotation.source,
            )
            for annotation in new_annotations
            if ("pseudo" not in annotation.tag and len(annotation.text.strip()) != 0)
        )


class RemoveAnnotations(dd.process.AnnotationProcessor):
    """Removes all annotations with corresponding tags."""

    def __init__(self, tags: list[str]) -> None:
        self.tags = tags

    def process_annotations(
        self, annotations: AnnotationSet, text: str
    ) -> AnnotationSet:
        return AnnotationSet(a for a in annotations if a.tag not in self.tags)


class CleanAnnotationTag(dd.process.AnnotationProcessor):
    """Cleans annotation tags based on the corresponding mapping."""

    def __init__(self, tag_map: dict[str, str]) -> None:
        self.tag_map = tag_map

    def process_annotations(
        self, annotations: AnnotationSet, text: str
    ) -> AnnotationSet:
        new_annotations = AnnotationSet()

        for annotation in annotations:
            if annotation.tag in self.tag_map:
                new_annotations.add(
                    dd.Annotation(
                        start_char=annotation.start_char,
                        end_char=annotation.end_char,
                        text=annotation.text,
                        start_token=annotation.start_token,
                        end_token=annotation.end_token,
                        tag=self.tag_map[annotation.tag],
                        priority=annotation.priority,
                        source=annotation.source,
                    )
                )
            else:
                new_annotations.add(annotation)

        return new_annotations
