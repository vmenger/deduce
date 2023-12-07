import docdeid as dd

from deduce.person import Person

text = (
    "betreft: Jan Jansen, bsn 111222333, patnr 000334433. De patient J. Jansen is 64 "
    "jaar oud en woonachtig in Utrecht. Hij werd op 10 oktober 2018 door arts "
    "Peter de Visser ontslagen van de kliniek van het UMCU. Voor nazorg kan hij "
    "worden bereikt via j.JNSEN.123@gmail.com of (06)12345678."
)


class TestDeduce:
    def test_annotate(self, model):
        metadata = {"patient": Person(first_names=["Jan"], surname="Jansen")}
        doc = model.deidentify(text, metadata=metadata)

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="(06)12345678",
                    start_char=272,
                    end_char=284,
                    tag="telefoonnummer",
                ),
                dd.Annotation(text="111222333", start_char=25, end_char=34, tag="bsn"),
                dd.Annotation(
                    text="Peter de Visser", start_char=153, end_char=168, tag="persoon"
                ),
                dd.Annotation(
                    text="j.JNSEN.123@gmail.com",
                    start_char=247,
                    end_char=268,
                    tag="email",
                ),
                dd.Annotation(
                    text="J. Jansen", start_char=64, end_char=73, tag="patient"
                ),
                dd.Annotation(
                    text="Jan Jansen", start_char=9, end_char=19, tag="patient"
                ),
                dd.Annotation(
                    text="10 oktober 2018", start_char=127, end_char=142, tag="datum"
                ),
                dd.Annotation(text="64", start_char=77, end_char=79, tag="leeftijd"),
                dd.Annotation(text="000334433", start_char=42, end_char=51, tag="id"),
                dd.Annotation(
                    text="Utrecht", start_char=106, end_char=113, tag="locatie"
                ),
                dd.Annotation(
                    text="UMCU", start_char=202, end_char=206, tag="instelling"
                ),
            ]
        )

        assert doc.annotations == set(expected_annotations)

    def test_deidentify(self, model):
        metadata = {"patient": Person(first_names=["Jan"], surname="Jansen")}
        doc = model.deidentify(text, metadata=metadata)

        expected_deidentified = (
            "betreft: [PATIENT], bsn [BSN-1], patnr [ID-1]. De patient [PATIENT] is "
            "[LEEFTIJD-1] jaar oud en woonachtig in [LOCATIE-1]. Hij werd op "
            "[DATUM-1] door arts [PERSOON-1] ontslagen van de kliniek van het "
            "[INSTELLING-1]. Voor nazorg kan hij worden bereikt via [EMAIL-1] "
            "of [TELEFOONNUMMER-1]."
        )

        assert doc.deidentified_text == expected_deidentified

    def test_annotate_intext(self, model):
        metadata = {"patient": Person(first_names=["Jan"], surname="Jansen")}
        doc = model.deidentify(text, metadata=metadata)

        expected_intext_annotated = (
            "betreft: <PATIENT>Jan Jansen</PATIENT>, bsn <BSN>111222333</BSN>, "
            "patnr <ID>000334433</ID>. De patient <PATIENT>J. Jansen</PATIENT> is "
            "<LEEFTIJD>64</LEEFTIJD> jaar oud en woonachtig in <LOCATIE>Utrecht"
            "</LOCATIE>. Hij werd op <DATUM>10 oktober 2018</DATUM> door arts "
            "<PERSOON>Peter de Visser</PERSOON> ontslagen van de kliniek van het "
            "<INSTELLING>UMCU</INSTELLING>. Voor nazorg kan hij worden bereikt "
            "via <EMAIL>j.JNSEN.123@gmail.com</EMAIL> of "
            "<TELEFOONNUMMER>(06)12345678</TELEFOONNUMMER>."
        )

        assert dd.utils.annotate_intext(doc) == expected_intext_annotated
