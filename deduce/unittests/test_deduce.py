import unittest

import docdeid

import deduce
import deduce.utility


class TestDeduceMethods(unittest.TestCase):
    def test_annotate_text(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotated = deduce.annotate_text(
            text=text, patient_first_names="Jan", patient_surname="Jansen"
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
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        expected_annotations = {
            docdeid.Annotation("Jan Jansen", 39, 49, "PATIENT"),
            docdeid.Annotation("patient J. Jansen", 54, 71, "PATIENT"),
            docdeid.Annotation("j.jnsen@email.com", 76, 93, "URL"),
            docdeid.Annotation("06-12345678", 98, 109, "TELEFOONNUMMER"),
            docdeid.Annotation("64", 114, 116, "LEEFTIJD"),
            docdeid.Annotation("Utrecht", 143, 150, "LOCATIE"),
            docdeid.Annotation("10 oktober", 164, 174, "DATUM"),
            docdeid.Annotation("Peter de Visser", 185, 200, "PERSOON"),
            docdeid.Annotation("UMCU", 234, 238, "INSTELLING"),
        }

        structured = deduce.deduce.annotate_text_structured(
            text, patient_first_names="Jan", patient_surname="Jansen"
        )

        assert len(expected_annotations) == len(structured)
        self.assertEqual(expected_annotations, set(structured))

    def test_leading_space(self):
        text = "\t Vandaag is Jan gekomen"
        annotations = deduce.annotate_text_structured(
            text=text,
            patient_first_names="Jan",
            patient_initials="J.",
            patient_surname="Janssen",
            patient_given_name="Jantinus",
        )

        self.assertEqual(1, len(annotations))
        self.assertEqual(docdeid.Annotation("Jan", 13, 16, "PATIENT"), annotations[0])

    def test_has_nested_tags_true(self):
        text = "<PERSOON Peter <INSTELLING Altrecht>>"
        self.assertTrue(deduce.utility.has_nested_tags(text))

    def test_has_nested_tags_false(self):
        text = "<PERSOON Peter> from <INSTELLING Altrecht>"
        self.assertFalse(deduce.utility.has_nested_tags(text))

    def test_has_nested_tags_error(self):
        text = "> Peter from Altrecht"
        self.assertRaises(ValueError, lambda: deduce.utility.has_nested_tags(text))

    def test_merge_adjacent_tags(self):
        text = "<PATIENT Jorge><PATIENT Ramos>"
        self.assertEqual(
            "<PATIENT JorgeRamos>", deduce.utility.merge_adjacent_tags(text)
        )

    def test_do_not_merge_adjacent_tags_with_different_categories(self):
        text = "<PATIENT Jorge><LOCATIE Ramos>"
        self.assertEqual(text, deduce.utility.merge_adjacent_tags(text))

    def test_merge_almost_adjacent_tags(self):
        text = "<PATIENT Jorge> <PATIENT Ramos>"
        self.assertEqual(
            "<PATIENT Jorge Ramos>", deduce.utility.merge_adjacent_tags(text)
        )


if __name__ == "__main__":
    unittest.main()
