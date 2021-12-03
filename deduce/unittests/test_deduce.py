import unittest

import deduce
from deduce.utilcls import Token, TokenGroup, Annotation


class TestDeduceMethods(unittest.TestCase):
    def test_annotate_text(self):

        text = (
            u"Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            u"(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            u"oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotated = deduce.annotate_text(
            text, patient_first_names="Jan", patient_surname="Jansen"
        )

        expected_text = (
            "Dit is stukje tekst met daarin de naam <PATIENT Jan Jansen>. De <PATIENT patient J. Jansen> "
            "(e: <URL j.jnsen@email.com>, t: <TELEFOONNUMMER 06-12345678>) is <LEEFTIJD 64> jaar oud en "
            "woonachtig in <LOCATIE Utrecht>. Hij werd op <DATUM 10 oktober> door arts "
            "<PERSOON Peter de Visser> ontslagen van de kliniek van het <INSTELLING UMCU>."
        )
        self.assertEqual(expected_text, annotated)

    def test_annotate_text_structured(self):
        text = (
            u"Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            u"(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            u"oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )
        mock_annotations = [
            Annotation(39, 49, "PATIENT", "Jan Jansen"),
            Annotation(54, 71, "PATIENT", "patient J. Jansen"),
            Annotation(76, 93, "URL", "j.jnsen@email.com"),
            Annotation(98, 109, "TELEFOONNUMMER", "06-12345678"),
            Annotation(114, 116, "LEEFTIJD", "64"),
            Annotation(143, 150, "LOCATIE", "Utrecht"),
            Annotation(164, 174, "DATUM", "10 oktober"),
            Annotation(185, 200, "PERSOON", "Peter de Visser"),
            Annotation(234, 238, "INSTELLING", "UMCU"),
        ]

        annotations = deduce.annotate_text_structured(text, patient_first_names="Jan", patient_surname="Jansen")
        self.assertEqual(mock_annotations, annotations)

    def test_leading_space(self):
        text = "\t Vandaag is Jan gekomen"
        annotations = deduce.annotate_text_structured(
            text, "Jan", "J.", "Janssen", "Jantinus"
        )
        self.assertEqual(1, len(annotations))
        self.assertEqual(Annotation(13, 16, "PATIENT", "Jan"), annotations[0])

    def test_has_nested_tags_true(self):
        spans = [TokenGroup([Token(0, 5, 'Peter', ''), Token(5, 6, ' ', ''), Token(6, 14, 'Altrecht', 'INSTELLING')],
                            'PERSOON')]
        self.assertTrue(deduce.deduce.has_nested_tags(spans))

    def test_has_nested_tags_false(self):
        spans = [Token(0, 5, 'Peter', 'PERSOON'), Token(5, 11, ' from ', ''), Token(11, 19, 'Altrecht', 'INSTELLING')]
        self.assertFalse(deduce.deduce.has_nested_tags(spans))

    def test_merge_adjacent_tags(self):
        spans = [Token(0, 5, 'Jorge', 'PATIENT'), Token(5, 10, 'Ramos', 'PATIENT')]
        merged = deduce.deduce.merge_adjacent_tags(spans)
        expected = [TokenGroup([Token(0, 5, 'Jorge', ''), Token(5, 10, 'Ramos', '')], 'PATIENT')]
        self.assertEqual(
            expected, merged
        )

    def test_do_not_merge_adjacent_tags_with_different_categories(self):
        spans = [Token(0, 5, 'Jorge', 'PATIENT'), Token(5, 10, 'Ramos', 'LOCATIE')]
        merged = deduce.deduce.merge_adjacent_tags(spans)
        expected = spans
        self.assertEqual(expected, merged)

    def test_merge_almost_adjacent_tags(self):
        spans = [Token(0, 5, 'Jorge', 'PATIENT'), Token(5, 6, ' ', ''), Token(6, 11, 'Ramos', 'PATIENT')]
        merged = deduce.deduce.merge_adjacent_tags(spans)
        expected = [TokenGroup([Token(0, 5, 'Jorge', ''), Token(5, 6, ' ', ''), Token(6, 11, 'Ramos', '')], 'PATIENT')]
        self.assertEqual(
            expected, merged
        )


if __name__ == "__main__":
    unittest.main()
