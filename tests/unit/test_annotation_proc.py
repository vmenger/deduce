import docdeid as dd

from deduce.annotation_processing import (
    CleanAnnotationTag,
    DeduceMergeAdjacentAnnotations,
    PersonAnnotationConverter,
    RemoveAnnotations,
)


class TestDeduceMergeAdjacent:
    def test_tags_match(self):
        proc = DeduceMergeAdjacentAnnotations()

        assert proc._tags_match("a", "a")
        assert proc._tags_match("huisnummer", "huisnummer")
        assert proc._tags_match("patient", "patient")
        assert proc._tags_match("persoon", "persoon")
        assert proc._tags_match("patient", "persoon")
        assert proc._tags_match("persoon", "patient")

        assert not proc._tags_match("a", "b")
        assert not proc._tags_match("patient", "huisnummer")
        assert not proc._tags_match("huisnummer", "patient")
        assert not proc._tags_match("persoon", "huisnummer")
        assert not proc._tags_match("huisnummer", "persoon")

    def test_annotation_replacement_equal_tags(self):
        proc = DeduceMergeAdjacentAnnotations()
        text = "Jan Jansen"
        left_annotation = dd.Annotation(
            text="Jan", start_char=0, end_char=3, tag="naam"
        )
        right_annotation = dd.Annotation(
            text="Jansen", start_char=4, end_char=10, tag="naam"
        )
        expected_annotation = dd.Annotation(
            text="Jan Jansen", start_char=0, end_char=10, tag="naam"
        )

        assert (
            proc._adjacent_annotations_replacement(
                left_annotation, right_annotation, text
            )
            == expected_annotation
        )

    def test_annotation_replacement_unequal_tags(self):
        proc = DeduceMergeAdjacentAnnotations()
        text = "Jan Jansen"
        left_annotation = dd.Annotation(
            text="Jan", start_char=0, end_char=3, tag="voornaam_patient"
        )
        right_annotation = dd.Annotation(
            text="Jansen", start_char=4, end_char=10, tag="achternaam_patient"
        )
        expected_annotation = dd.Annotation(
            text="Jan Jansen", start_char=0, end_char=10, tag="patient"
        )

        assert (
            proc._adjacent_annotations_replacement(
                left_annotation, right_annotation, text
            )
            == expected_annotation
        )


class TestPersonAnnotationConverter:
    def test_patient_no_overlap(self):
        proc = PersonAnnotationConverter()
        text = "Jan Jansen"

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Jan", start_char=0, end_char=3, tag="voornaam_patient"
                ),
                dd.Annotation(
                    text="Jansen", start_char=4, end_char=10, tag="achternaam_patient"
                ),
            ]
        )

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation(text="Jan", start_char=0, end_char=3, tag="patient"),
                dd.Annotation(text="Jansen", start_char=4, end_char=10, tag="patient"),
            ]
        )

        assert proc.process_annotations(annotations, text) == expected_annotations

    def test_patient_with_overlap(self):
        proc = PersonAnnotationConverter()
        text = "Jan Jansen"

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Jan", start_char=0, end_char=3, tag="voornaam_patient"
                ),
                dd.Annotation(
                    text="Jan Jansen", start_char=0, end_char=10, tag="naam_patient"
                ),
            ]
        )

        expected_annotations = dd.AnnotationSet(
            [dd.Annotation(text="Jan Jansen", start_char=0, end_char=10, tag="patient")]
        )

        assert proc.process_annotations(annotations, text) == expected_annotations

    def test_mixed_no_overlap(self):
        proc = PersonAnnotationConverter()
        text = "Jan Jansen"

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Jan", start_char=0, end_char=3, tag="voornaam_patient"
                ),
                dd.Annotation(
                    text="Jansen", start_char=4, end_char=10, tag="achternaam_onbekend"
                ),
            ]
        )

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation(text="Jan", start_char=0, end_char=3, tag="patient"),
                dd.Annotation(text="Jansen", start_char=4, end_char=10, tag="persoon"),
            ]
        )

        assert proc.process_annotations(annotations, text) == expected_annotations

    def test_mixed_with_overlap(self):
        proc = PersonAnnotationConverter()
        text = "Jan Jansen"

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Jan", start_char=0, end_char=3, tag="voornaam_patient"
                ),
                dd.Annotation(
                    text="Jan Jansen", start_char=0, end_char=10, tag="naam_onbekend"
                ),
            ]
        )

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation(text="Jan", start_char=0, end_char=3, tag="patient"),
                dd.Annotation(text=" Jansen", start_char=3, end_char=10, tag="persoon"),
            ]
        )

        assert proc.process_annotations(annotations, text) == expected_annotations


class TestRemoveAnnotations:
    def test_remove_annotations(self):

        ra = RemoveAnnotations(tags=["voornaam_patient", "nonexisting_tag"])

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Jan", start_char=0, end_char=3, tag="voornaam_patient"
                ),
                dd.Annotation(
                    text="Jansen", start_char=4, end_char=10, tag="achternaam_patient"
                ),
            ]
        )

        processed_annotations = ra.process_annotations(annotations, text="_")

        assert processed_annotations == dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Jansen", start_char=4, end_char=10, tag="achternaam_patient"
                )
            ]
        )


class TestCleanAnnotationTag:
    def test_remove_annotations(self):

        cat = CleanAnnotationTag(
            tag_map={"voornaam_patient": "voornaam", "nonexistent": "test"}
        )

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Jan", start_char=0, end_char=3, tag="voornaam_patient"
                ),
                dd.Annotation(
                    text="Jansen", start_char=4, end_char=10, tag="achternaam_patient"
                ),
            ]
        )

        processed_annotations = cat.process_annotations(annotations, text="_")

        assert processed_annotations == dd.AnnotationSet(
            [
                dd.Annotation(text="Jan", start_char=0, end_char=3, tag="voornaam"),
                dd.Annotation(
                    text="Jansen", start_char=4, end_char=10, tag="achternaam_patient"
                ),
            ]
        )
