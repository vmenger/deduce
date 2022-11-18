import docdeid as dd


class DeduceMergeAdjacentAnnotations(dd.process.MergeAdjacentAnnotations):
    def _tags_match(self, left_tag: str, right_tag: str) -> bool:

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
