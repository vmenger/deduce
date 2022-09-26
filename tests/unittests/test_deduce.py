import unittest

import docdeid

import deduce
from deduce.deduce import Deduce
from deduce.annotate import Person


class TestDeduceMethods(unittest.TestCase):

    def setUp(self) -> None:

        self.deduce = Deduce()

    def test_annotate(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        meta_data = {
            "patient": Person(
                first_names=['Jan'],
                surname='Jansen'
            )
        }

        expected_annotations = {
            docdeid.Annotation("Jan Jansen", 39, 49, "patient"),
            docdeid.Annotation("patient J. Jansen", 54, 71, "patient"),
            docdeid.Annotation("j.jnsen@email.com", 76, 93, "url"),
            docdeid.Annotation("06-12345678", 98, 109, "telefoonnummer"),
            docdeid.Annotation("64", 114, 116, "leeftijd"),
            docdeid.Annotation("Utrecht", 143, 150, "locatie"),
            docdeid.Annotation("10 oktober", 164, 174, "datum"),
            docdeid.Annotation("Peter de Visser", 185, 200, "persoon"),
            docdeid.Annotation("UMCU", 234, 238, "instelling"),
        }

        annotations = self.deduce.deidentify(text=text, meta_data=meta_data).annotations

        assert len(expected_annotations) == len(annotations)
        self.assertEqual(expected_annotations, annotations)

    def test_deidentify(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        meta_data = {
            "patient": Person(
                first_names=['Jan'],
                surname='Jansen'
            )
        }

        doc = self.deduce.deidentify(text=text, meta_data=meta_data)

        expected_text = (
            "Dit is stukje tekst met daarin de naam <PATIENT>. De <PATIENT> (e: <URL-1>, t: <TELEFOONNUMMER-1>) "
            "is <LEEFTIJD-1> jaar oud en woonachtig in <LOCATIE-1>. Hij werd op <DATUM-1> door arts <PERSOON-1> "
            "ontslagen van de kliniek van het <INSTELLING-1>."
        )

        self.assertEqual(expected_text, doc.deidentified_text)

    def test_annotate_backwardscompat(self):

            text = (
                "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
                "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
                "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
            )

            annotated = deduce.annotate_text(
                text=text, patient_first_names="Jan", patient_surname="Jansen", patient_initials="J", patient_given_name="Jantinus"
            )

            expected_text = (
                "Dit is stukje tekst met daarin de naam <PATIENT Jan Jansen>. De <PATIENT patient J. Jansen> "
                "(e: <URL j.jnsen@email.com>, t: <TELEFOONNUMMER 06-12345678>) is <LEEFTIJD 64> jaar oud en "
                "woonachtig in <LOCATIE Utrecht>. Hij werd op <DATUM 10 oktober> door arts "
                "<PERSOON Peter de Visser> ontslagen van de kliniek van het <INSTELLING UMCU>."
            )
            self.assertEqual(expected_text, annotated)


    def test_leading_space(self):

        text = "\t Vandaag is Jan gekomen"

        meta_data = {
            "patient": Person(
                first_names=['Jan'],
                surname='Jansen',
                initials='J',
                given_name='Jantinus'
            )
        }

        annotations = self.deduce.deidentify(text=text, meta_data=meta_data).annotations

        self.assertEqual(1, len(annotations))
        self.assertTrue(docdeid.Annotation("Jan", 13, 16, "patient") in annotations)


if __name__ == "__main__":
    unittest.main()
