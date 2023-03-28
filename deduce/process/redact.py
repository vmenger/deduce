import docdeid as dd
from rapidfuzz.distance import DamerauLevenshtein


class DeduceRedactor(dd.process.SimpleRedactor):
    """
    Implements the redacting logic of Deduce:

    - All annotations with "patient" tag are replaced with <PATIENT>
    - All other annotations are replaced with <TAG-n>, with n identifying a group of annotations with
        a similar text (edit_distance <= 1).
    """

    def redact(self, text: str, annotations: dd.AnnotationSet) -> str:
        annotations_to_intext_replacement = {}

        for tag, annotation_group in self._group_annotations_by_tag(annotations).items():

            annotations_to_replacement_group: dict[dd.Annotation, str] = {}
            counter = 1

            for annotation in sorted(annotation_group, key=lambda a: a.get_sort_key(by=["end_char"])):

                if tag == "patient":

                    annotations_to_intext_replacement[annotation] = f"{self.open_char}" f"PATIENT" f"{self.close_char}"

                else:

                    match = False

                    # Check match with any
                    for annotation_match, replacement in annotations_to_replacement_group.items():

                        if DamerauLevenshtein.distance(annotation.text, annotation_match.text, score_cutoff=1) <= 1:

                            annotations_to_replacement_group[annotation] = replacement
                            match = True
                            break

                    if not match:

                        annotations_to_replacement_group[annotation] = (
                            f"{self.open_char}" f"{annotation.tag.upper()}" f"-" f"{counter}" f"{self.close_char}"
                        )

                        counter += 1

                annotations_to_intext_replacement |= annotations_to_replacement_group

        return self._replace_annotations_in_text(text, annotations, annotations_to_intext_replacement)
