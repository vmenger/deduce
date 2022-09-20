import docdeid
from docdeid.annotate.annotation_processor import MergeAdjacentAnnotations


class DeduceMergeAdjacentAnnotations(MergeAdjacentAnnotations):
    def _tags_match(self, left_tag: str, right_tag: str):

        return (left_tag == right_tag) or {left_tag, right_tag} == {
            "patient",
            "persoon",
        }

    def _adjacent_annotations_replacement(
        self,
        left_annotation: docdeid.Annotation,
        right_annotation: docdeid.Annotation,
        text: str,
    ) -> docdeid.Annotation:

        if left_annotation.tag != right_annotation.tag:
            replacement_tag = "patient"
        else:
            replacement_tag = left_annotation.tag

        return docdeid.Annotation(
            text=text[left_annotation.start_char : right_annotation.end_char],
            start_char=left_annotation.start_char,
            end_char=right_annotation.end_char,
            tag=replacement_tag,
        )
