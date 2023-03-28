import docdeid as dd


class DeduceMergeAdjacentAnnotations(dd.process.MergeAdjacentAnnotations):
    """
    Merge adjacent tags, according to deduce logic:

    - adjacent annotations with mixed patient/person tags are replaced with a patient annotation
    """

    def _tags_match(self, left_tag: str, right_tag: str) -> bool:
        """
        Define whether two tags match. This is the case when they are equal strings, and additionally patient and person
        tags are also regarded as equal.

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

        If one of the two annotations has the patient tag, the new annotation will also be tagged patient. In other
        cases, the tags are already equal.
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
    Responsible for processing the annotations produced by all name annotators (regular and context-based).

    Resolves overlap between them, and then maps the tags to either "patient" or "persoon", based on whether "patient"
    is in the tag (e.g. voornaam_patient => patient, achternaam_onbekend => persoon).
    """

    def __init__(self) -> None:
        self._overlap_resolver = dd.process.OverlapResolver(
            sort_by=["tag", "length"],
            sort_by_callbacks={"tag": lambda x: "patient" not in x, "length": lambda x: -x},
        )

    def process_annotations(self, annotations: dd.AnnotationSet, text: str) -> dd.AnnotationSet:
        new_annotations = self._overlap_resolver.process_annotations(annotations, text=text)

        return dd.AnnotationSet(
            dd.Annotation(
                text=annotation.text,
                start_char=annotation.start_char,
                end_char=annotation.end_char,
                tag="patient" if "patient" in annotation.tag else "persoon",
            )
            for annotation in new_annotations
        )
