""" Just making sure it doesn't break. No need to spend much time updating this. """

import docdeid as dd

from deduce import annotate_text, annotate_text_structured, deidentify_annotations

text = (
    "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
    "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
    "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
)


class TestBackwardsCompat:
    def test_annotate_text(self):

        annotated = annotate_text(text, patient_first_names="Jan", patient_surname="Jansen")

        expected_annotated = (
            "Dit is stukje tekst met daarin de naam <PATIENT Jan Jansen>. De <PATIENT patient J. Jansen> "
            "(e: <URL j.jnsen@email.com>, t: <TELEFOONNUMMER 06-12345678>) is <LEEFTIJD 64> jaar oud en "
            "woonachtig in <LOCATIE Utrecht>. Hij werd op <DATUM 10 oktober> door arts "
            "<PERSOON Peter de Visser> ontslagen van de kliniek van het <INSTELLING UMCU>."
        )

        assert annotated == expected_annotated

    def test_annotate_text_structured(self):

        annotations = annotate_text_structured(text, patient_first_names="Jan", patient_surname="Jansen")

        expected_annotations = [
            dd.Annotation("Jan Jansen", 39, 49, "patient"),
            dd.Annotation("patient J. Jansen", 54, 71, "patient"),
            dd.Annotation("j.jnsen@email.com", 76, 93, "url"),
            dd.Annotation("06-12345678", 98, 109, "telefoonnummer"),
            dd.Annotation("64", 114, 116, "leeftijd"),
            dd.Annotation("Utrecht", 143, 150, "locatie"),
            dd.Annotation("10 oktober", 164, 174, "datum"),
            dd.Annotation("Peter de Visser", 185, 200, "persoon"),
            dd.Annotation("UMCU", 234, 238, "instelling"),
        ]

        assert set(annotations) == set(expected_annotations)

    def test_deidentify_annotations(self):

        annotated = annotate_text(text, patient_first_names="Jan", patient_surname="Jansen")
        deidentified = deidentify_annotations(annotated)

        expected_deidentified = (
            "Dit is stukje tekst met daarin de naam <PATIENT>. De <PATIENT> (e: <URL-1>, t: <TELEFOONNUMMER-1>) "
            "is <LEEFTIJD-1> jaar oud en woonachtig in <LOCATIE-1>. Hij werd op <DATUM-1> door arts <PERSOON-1> "
            "ontslagen van de kliniek van het <INSTELLING-1>."
        )

        assert deidentified == expected_deidentified
