import docdeid
from docdeid.annotation.redactor import BaseRedactor
from nltk import edit_distance


class DeduceRedactor(BaseRedactor):
    """Copies the logic from deidentify_annotations"""

    @staticmethod
    def _filter_annotations_by_category(
        annotations: list[docdeid.Annotation], category: str
    ):
        return [
            annotation for annotation in annotations if annotation.category == category
        ]

    def redact(self, text: str, annotations: list[docdeid.Annotation]) -> str:

        annotations = sorted(
            annotations, key=lambda a: a.get_sort_key(by=["end_char", "category"])
        )
        annotations_to_replacement = {}

        other_annotations = []

        for annotation in annotations:

            if annotation.category == "PATIENT":
                annotations_to_replacement[annotation] = "<PATIENT>"
            else:
                other_annotations.append(annotation)

        for tagname in [
            "PERSOON",
            "LOCATIE",
            "INSTELLING",
            "DATUM",
            "LEEFTIJD",
            "PATIENTNUMMER",
            "TELEFOONNUMMER",
            "URL",
        ]:

            annotations_subset = self._filter_annotations_by_category(
                annotations, tagname
            )
            annotations_to_replacement_tag = {}
            dispenser = 1

            for annotation in annotations_subset:

                match = False

                # Check match with any
                for annotation_match in annotations_to_replacement_tag.keys():

                    if edit_distance(annotation.text, annotation_match.text) <= 1:
                        annotations_to_replacement_tag[
                            annotation
                        ] = annotations_to_replacement_tag[annotation_match]
                        match = True
                        break

                if not match:
                    annotations_to_replacement_tag[
                        annotation
                    ] = f"<{tagname}-{dispenser}>"
                    dispenser += 1

            annotations_to_replacement |= annotations_to_replacement_tag

        assert len(annotations_to_replacement) == len(annotations)

        sorted_annotations = sorted(
            annotations,
            key=lambda a: a.get_sort_key(
                by=["end_char", "category"], callbacks={"end_char": lambda x: -x}
            ),
        )

        for annotation in sorted_annotations:

            text = (
                text[: annotation.start_char]
                + annotations_to_replacement[annotation]
                + text[annotation.end_char :]
            )

        return text
