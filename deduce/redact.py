import docdeid
from docdeid.annotation.redactor import BaseRedactor
from nltk import edit_distance

from collections import defaultdict
from typing import Any, Type


class DeduceRedactor(BaseRedactor):
    """Copies the logic from deidentify_annotations"""

    @staticmethod
    def _group_annotations(annotations: list[docdeid.Annotation]) -> defaultdict[Any, list]:

        category_to_list = defaultdict(list)

        for annotation in annotations:
            category_to_list[annotation.category].append(annotation)

        return category_to_list

    def redact(self, text: str, annotations: list[docdeid.Annotation]) -> str:

        annotations_to_intext_replacement = {}

        for category, annotation_group in self._group_annotations(annotations).items():

            # print(category, annotation_group)

            annotations_to_replacement_group = {}
            dispenser = 1

            for annotation in sorted(annotation_group, key=lambda a: a.get_sort_key(by=['end_char'])):

                if category == "patient":

                    annotations_to_intext_replacement[annotation] = "<PATIENT>"

                else:

                    match = False

                    # Check match with any
                    for annotation_match in annotations_to_replacement_group.keys():

                        # print(annotation, annotation_match)

                        if edit_distance(annotation.text, annotation_match.text) <= 1:

                            annotations_to_replacement_group[
                                annotation
                            ] = annotations_to_replacement_group[annotation_match]
                            match = True
                            break

                    if not match:

                        annotations_to_replacement_group[
                            annotation
                        ] = f"<{annotation.category.upper()}-{dispenser}>"
                        dispenser += 1

                        # print(annotations_to_replacement_group, dispenser)

                annotations_to_intext_replacement |= annotations_to_replacement_group

        assert len(annotations_to_intext_replacement) == len(annotations)

        sorted_annotations = sorted(
            annotations,
            key=lambda a: a.get_sort_key(
                by=["end_char"], callbacks={"end_char": lambda x: -x}
            ),
        )

        for annotation in sorted_annotations:

            text = (
                text[: annotation.start_char]
                + annotations_to_intext_replacement[annotation]
                + text[annotation.end_char :]
            )

        return text
