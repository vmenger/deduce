import docdeid
from docdeid.annotation.annotation_processor import MergeAdjacentAnnotations


class DeduceMergeAdjacentAnnotations(MergeAdjacentAnnotations):
    def _matching_categories(self, left_category: str, right_category: str):

        return (left_category == right_category) or {left_category, right_category} == {
            "PATIENT",
            "PERSOON",
        }

    def _adjacent_annotations_replacement(
        self,
        left_annotation: docdeid.Annotation,
        right_annotation: docdeid.Annotation,
        text: str,
    ) -> docdeid.Annotation:

        if left_annotation.category != right_annotation.category:
            replacement_category = "PATIENT"
        else:
            replacement_category = left_annotation.category

        return docdeid.Annotation(
            text=text[left_annotation.start_char : right_annotation.end_char],
            start_char=left_annotation.start_char,
            end_char=right_annotation.end_char,
            category=replacement_category,
        )
