import unittest
from unittest.mock import patch

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
        annotated_text = (
            "Dit is stukje tekst met daarin de naam <PERSOON Jan Jansen>. De "
            "<PERSOON patient J. Jansen> (e: <URL j.jnsen@email.com>, t: <TELEFOONNUMMER 06-12345678>) "
            "is <LEEFTIJD 64> jaar oud en woonachtig in <LOCATIE Utrecht>. Hij werd op "
            "<DATUM 10 oktober> door arts <PERSOON Peter de Visser> ontslagen van de kliniek van het "
            "<INSTELLING umcu>."
        )
        mock_tags = [
            "<PERSOON Jan Jansen>",
            "<PERSOON patient J. Jansen>",
            "<URL j.jnsen@email.com>",
            "<TELEFOONNUMMER 06-12345678>",
            "<LEEFTIJD 64>",
            "<LOCATIE Utrecht>",
            "<DATUM 10 oktober>",
            "<PERSOON Peter de Visser>",
            "<INSTELLING umcu>",
        ]
        mock_annotations = [
            Annotation(39, 49, "PATIENT", "Jan Jansen"),
            Annotation(62, 71, "PATIENT", "J. Jansen"),
            Annotation(76, 93, "URL", "j.jnsen@email.com"),
            Annotation(98, 109, "TELEFOONNUMMER", "06-12345678"),
            Annotation(114, 116, "LEEFTIJD", "64"),
            Annotation(143, 150, "LOCATIE", "Utrecht"),
            Annotation(164, 174, "DATUM", "10 oktober"),
            Annotation(185, 200, "PERSOON", "Peter de Visser"),
            Annotation(234, 238, "INSTELLING", "umcu"),
        ]

        def mock_annotate_text(
            mock_text: str,
            patient_first_names="",
            patient_initials="",
            patient_surname="",
            patient_given_name="",
            names=True,
            locations=True,
            institutions=True,
            dates=True,
            ages=True,
            patient_numbers=True,
            phone_numbers=True,
            urls=True,
            flatten=True,
        ):
            return annotated_text if mock_text == text else ""

        def mock_find_tags(tt):
            return mock_tags if tt == annotated_text else []

        def mock_get_annotations(ttext, ttags, tn):
            return (
                mock_annotations
                if ttext == annotated_text and ttags == mock_tags and tn == 0
                else []
            )

        def mock_get_first_non_whitespace(tt):
            return 0 if tt == text else -1

        with patch.object(
            deduce.deduce, "annotate_text", side_effect=mock_annotate_text
        ) as _:
            with patch.object(
                deduce.utility, "find_tags", side_effect=mock_find_tags
            ) as _:
                with patch.object(
                    deduce.utility, "get_annotations", side_effect=mock_get_annotations
                ) as _:
                    with patch.object(
                        deduce.utility,
                        "get_first_non_whitespace",
                        side_effect=mock_get_first_non_whitespace,
                    ) as _:
                        structured = deduce.deduce.annotate_text_structured(
                            text, patient_first_names="Jan", patient_surname="Jansen"
                        )
        self.assertEqual(mock_annotations, structured)

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
