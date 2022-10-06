from collections import defaultdict

import docdeid
from docdeid.annotate.redactor import BaseRedactor
from rapidfuzz.distance import DamerauLevenshtein


class DeduceRedactor(BaseRedactor):
    """Copies the logic from deidentify_annotations"""

    @staticmethod
    def _group_annotations(
        annotations: list[docdeid.Annotation],
    ) -> defaultdict[str, list]:

        tag_to_list = defaultdict(list)

        for annotation in annotations:
            tag_to_list[annotation.tag].append(annotation)

        return tag_to_list

    def redact(self, text: str, annotations: list[docdeid.Annotation]) -> str:

        annotations_to_intext_replacement = {}

        for tag, annotation_group in self._group_annotations(annotations).items():

            annotations_to_replacement_group = {}
            dispenser = 1

            for annotation in sorted(annotation_group, key=lambda a: a.get_sort_key(by=["end_char"])):

                if tag == "patient":

                    annotations_to_intext_replacement[annotation] = "<PATIENT>"

                else:

                    match = False

                    # Check match with any
                    for annotation_match in annotations_to_replacement_group.keys():

                        if DamerauLevenshtein.distance(annotation.text, annotation_match.text, score_cutoff=1) <= 1:

                            annotations_to_replacement_group[annotation] = annotations_to_replacement_group[
                                annotation_match
                            ]
                            match = True
                            break

                    if not match:

                        annotations_to_replacement_group[annotation] = f"<{annotation.tag.upper()}-{dispenser}>"
                        dispenser += 1

                annotations_to_intext_replacement |= annotations_to_replacement_group

        assert len(annotations_to_intext_replacement) == len(annotations)

        sorted_annotations = sorted(
            annotations,
            key=lambda a: a.get_sort_key(by=["end_char"], callbacks={"end_char": lambda x: -x}),
        )

        for annotation in sorted_annotations:

            text = (
                text[: annotation.start_char]
                + annotations_to_intext_replacement[annotation]
                + text[annotation.end_char :]
            )

        return text
