"""Contains components for processing AnnotationSet."""

import docdeid as dd
from docdeid import AnnotationSet
from frozendict import frozendict


class DeduceMergeAdjacentAnnotations(dd.process.MergeAdjacentAnnotations):
    """
    Merges adjacent tags, according to Deduce logic:

    - adjacent annotations with mixed patient/person tags are replaced
      with the "persoon" annotation;
    - adjacent annotations with patient tags of which one is the surname
      are replaced with the "patient" annotation; and
    - adjacent annotations with other patient tags are replaced with
      the "part_of_patient" annotation.
    """

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

        patient_part = [tag.endswith("_patient") for tag in (left_tag, right_tag)]
        # FIXME Ideally, we should be first looking for a `*_patient` tag in
        #  both directions and only failing that, merge with an adjacent
        #  "persoon" tag.
        return (
            left_tag == right_tag
            or all(patient_part)
            or (patient_part[0] and right_tag == "persoon")
        )

    def _adjacent_annotations_replacement(
        self,
        left_annotation: dd.Annotation,
        right_annotation: dd.Annotation,
        text: str,
    ) -> dd.Annotation:
        """
        Replace two annotations that have equal tags with a new annotation.

        If one of the two annotations has the "patient" tag (and the other is either
        "patient" or "persoon"), the other annotation will be used. In other cases, the
        tags are always equal.
        """

        ltag = left_annotation.tag
        rtag = right_annotation.tag
        replacement_tag = (
            ltag
            if ltag == rtag
            else "persoon"
            if rtag == "persoon"
            else "patient"
            if any(tag.startswith("achternaam") for tag in (ltag, rtag))
            else "part_of_patient"
        )

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

    Any overlap with annotations that contain "pseudo" in their tag is removed, as are
    those annotations. Then resolves overlap between remaining annotations, and maps the
    tags to either "patient" or "persoon", based on whether "patient" is in all
    constituent tags (e.g. voornaam_patient+achternaam_patient => patient,
    achternaam_onbekend => persoon).
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

        real_annos = (
            anno
            for anno in new_annotations
            if "pseudo" not in anno.tag and anno.text.strip()
        )
        with_patient = (
            dd.Annotation(
                text=anno.text,
                start_char=anno.start_char,
                end_char=anno.end_char,
                tag=PersonAnnotationConverter._resolve_tag(anno.tag),
            )
            for anno in real_annos
        )
        return dd.AnnotationSet(with_patient)

    @classmethod
    def _resolve_tag(cls, tag: str) -> str:
        if "+" not in tag:
            return tag if "patient" in tag else "persoon"
        return (
            "patient"
            if all("patient" in part for part in tag.split("+"))
            else "persoon"
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
    """Renames tags using a mapping."""

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
                    )
                )
            else:
                new_annotations.add(annotation)

        return new_annotations
