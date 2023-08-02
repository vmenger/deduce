import docdeid as dd

from deduce import Deduce
from deduce.person import Person

text = (
    "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
    "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
    "oktober 2018 door arts Peter de Visser ontslagen van de kliniek van het UMCU."
)


class TestDeduce:
    def test_annotate(self):
        deduce = Deduce()
        person = Person(first_names=["Jan"], surname="Jansen")
        doc = deduce.deidentify(text, metadata={"patient": person})

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation("Jan Jansen", 39, 49, "patient"),
                dd.Annotation("patient J. Jansen", 54, 71, "patient"),
                dd.Annotation("j.jnsen@email.com", 76, 93, "email"),
                dd.Annotation("06-12345678", 98, 109, "telefoonnummer"),
                dd.Annotation("64", 114, 116, "leeftijd"),
                dd.Annotation("Utrecht", 143, 150, "locatie"),
                dd.Annotation("10 oktober 2018", 164, 179, "datum"),
                dd.Annotation("Peter de Visser", 190, 205, "persoon"),
                dd.Annotation("UMCU", 239, 243, "instelling"),
            ]
        )

        assert doc.annotations == set(expected_annotations)

    def test_deidentify(self):
        deduce = Deduce()
        person = Person(first_names=["Jan"], surname="Jansen")
        doc = deduce.deidentify(text, metadata={"patient": person})

        expected_deidentified = (
            "Dit is stukje tekst met daarin de naam <PATIENT>. De <PATIENT> (e: <EMAIL-1>, t: <TELEFOONNUMMER-1>) "
            "is <LEEFTIJD-1> jaar oud en woonachtig in <LOCATIE-1>. Hij werd op <DATUM-1> door arts <PERSOON-1> "
            "ontslagen van de kliniek van het <INSTELLING-1>."
        )

        assert doc.deidentified_text == expected_deidentified

    def test_annotate_intext(self):
        deduce = Deduce()
        person = Person(first_names=["Jan"], surname="Jansen")
        doc = deduce.deidentify(text, metadata={"patient": person})

        print(dd.utils.annotate_intext(doc))

        expected_intext_annotated = (
            "Dit is stukje tekst met daarin de naam <PATIENT>Jan Jansen</PATIENT>. "
            "De <PATIENT>patient J. Jansen</PATIENT> (e: <EMAIL>j.jnsen@email.com</EMAIL>, "
            "t: <TELEFOONNUMMER>06-12345678</TELEFOONNUMMER>) is <LEEFTIJD>64</LEEFTIJD> jaar oud "
            "en woonachtig in <LOCATIE>Utrecht</LOCATIE>. Hij werd op <DATUM>10 oktober 2018</DATUM> door "
            "arts <PERSOON>Peter de Visser</PERSOON> ontslagen van de kliniek van het <INSTELLING>UMCU</INSTELLING>."
        )

        assert dd.utils.annotate_intext(doc) == expected_intext_annotated
