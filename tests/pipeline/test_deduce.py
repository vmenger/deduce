import docdeid as dd
import pytest

from deduce import Deduce
from deduce.person import Person

text = (
    "betreft: Jan Jansen, bsn 111222333, patnr 000334433. De patient J. Jansen is 64 "
    "jaar oud en woonachtig in Utrecht, IJSWEG 10r. Hij werd op 10 oktober 2018 door arts "
    "Peter de Visser ontslagen van de kliniek van het UMCU. Voor nazorg kan hij "
    "worden bereikt via j.JNSEN.123@gmail.com of (06)12345678. "
    "Vader, Peter Jansen, 104 jr, woont ook in Utrecht. Met collegiale groeten, "
    "Jan de Visser."
    # FIXME "aan de" is joined to one token (due to "lst_interfix/items.txt"),
    #   preventing "de Quervain ziekte" from matching. Furthermore, when I
    #   managed to get this term censored, the "aan" word was censored, too.
    #   Use a simple whitespace/punctuation-based tokenizer for that annotator
    #   to fix this issue.
    # " De patient lijdt aan de Quervain ziekte."
)


@pytest.fixture
def model(shared_datadir):
    return Deduce(
        save_lookup_structs=False,
        build_lookup_structs=True,
        lookup_data_path=shared_datadir / "lookup",
    )


class TestDeduce:
    def test_annotate(self, model):
        metadata = {"patient": Person(first_names=["Jan"], surname="Jansen")}
        doc = model.deidentify(text, metadata=metadata)

        expected_annotations = {
            dd.Annotation(
                text="(06)12345678",
                start_char=284,
                end_char=296,
                tag="telefoonnummer",
            ),
            dd.Annotation(text="111222333", start_char=25, end_char=34, tag="bsn"),
            dd.Annotation(
                text="Peter de Visser", start_char=165, end_char=180, tag="persoon"
            ),
            dd.Annotation(
                text="j.JNSEN.123@gmail.com",
                start_char=259,
                end_char=280,
                tag="emailadres",
            ),
            dd.Annotation(text="J. Jansen", start_char=64, end_char=73, tag="patient"),
            dd.Annotation(text="Jan Jansen", start_char=9, end_char=19, tag="patient"),
            dd.Annotation(
                text="10 oktober 2018", start_char=139, end_char=154, tag="datum"
            ),
            dd.Annotation(text="64", start_char=77, end_char=79, tag="leeftijd"),
            dd.Annotation(text="000334433", start_char=42, end_char=51, tag="id"),
            dd.Annotation(text="Utrecht", start_char=106, end_char=113, tag="locatie"),
            dd.Annotation(
                text="IJSWEG 10r", start_char=115, end_char=125, tag="locatie"
            ),
            dd.Annotation(text="UMCU", start_char=214, end_char=218, tag="ziekenhuis"),
            dd.Annotation(
                text="Peter Jansen", start_char=305, end_char=317, tag="persoon"
            ),
            dd.Annotation(text="104", start_char=319, end_char=322, tag="leeftijd"),
            dd.Annotation(text="Utrecht", start_char=340, end_char=347, tag="locatie"),
            dd.Annotation(
                text="Jan de Visser", start_char=373, end_char=386, tag="persoon"
            ),
        }

        assert set(doc.annotations) == expected_annotations

    def test_deidentify(self, model):
        metadata = {"patient": Person(first_names=["Jan"], surname="Jansen")}
        doc = model.deidentify(text, metadata=metadata)

        expected_deidentified = (
            "betreft: [PATIENT], bsn [BSN-1], patnr [ID-1]. De patient [PATIENT] is "
            "[LEEFTIJD-1] jaar oud en woonachtig in [LOCATIE-1], [LOCATIE-2]. Hij werd "
            "op [DATUM-1] door arts [PERSOON-1] ontslagen van de kliniek van het "
            "[ZIEKENHUIS-1]. Voor nazorg kan hij worden bereikt via [EMAILADRES-1] "
            "of [TELEFOONNUMMER-1]. Vader, [PERSOON-2], [LEEFTIJD-2] jr, woont "
            # XXX Btw, if we wanted more perfect security, we should
            #   not give away whether two mentions of age (or street or
            #   anything) were equal before deidentification or not.
            #   Concretely, it shouldn't matter whether LEEFTIJD-1 is the same
            #   as LEEFTIJD-2.
            "ook in [LOCATIE-1]. Met collegiale groeten, [PERSOON-3]."
        )

        assert doc.deidentified_text == expected_deidentified

    def test_annotate_intext(self, model):
        metadata = {"patient": Person(first_names=["Jan"], surname="Jansen")}
        doc = model.deidentify(text, metadata=metadata)

        expected_intext_annotated = (
            "betreft: <PATIENT>Jan Jansen</PATIENT>, bsn <BSN>111222333</BSN>, "
            "patnr <ID>000334433</ID>. De patient <PATIENT>J. Jansen</PATIENT> is "
            "<LEEFTIJD>64</LEEFTIJD> jaar oud en woonachtig in <LOCATIE>Utrecht"
            "</LOCATIE>, <LOCATIE>IJSWEG 10r</LOCATIE>. Hij werd op <DATUM>10 "
            "oktober 2018</DATUM> door arts <PERSOON>Peter de "
            "Visser</PERSOON> ontslagen van de kliniek van het "
            "<ZIEKENHUIS>UMCU</ZIEKENHUIS>. Voor nazorg kan hij worden "
            "bereikt via <EMAILADRES>j.JNSEN.123@gmail.com</EMAILADRES> of "
            "<TELEFOONNUMMER>(06)12345678</TELEFOONNUMMER>."
            # " De patient lijdt aan de Quervain ziekte."
            " Vader, <PERSOON>Peter Jansen</PERSOON>, "
            "<LEEFTIJD>104</LEEFTIJD> jr, woont ook in "
            "<LOCATIE>Utrecht</LOCATIE>. Met collegiale groeten, "
            "<PERSOON>Jan de Visser</PERSOON>."
        )

        assert dd.utils.annotate_intext(doc) == expected_intext_annotated

    def test_patient_2(self, model):
        metadata = {"patient": Person(first_names=["Jan"], surname="Jansen")}
        doc = (
            "Lorem ipsum JANSEN sit amet, Peter Jansen adipiscing elit. "
            "Curabitur J. Jansen sapien, J. P. Jansen a vestibulum quis, "
            "facilisis vel J Jansen. Jan de Visser iaculis gravida nulla. "
            "Etiam quis Jan van den Jansen."
        )
        want = (
            "Lorem ipsum [PATIENT] sit amet, [PERSOON-1] adipiscing elit. "
            "Curabitur [PATIENT] sapien, [PERSOON-2] a vestibulum quis, "
            "facilisis vel [PATIENT]. [PERSOON-3] iaculis gravida nulla. "
            "Etiam quis [PERSOON-4]."
        )

        deid = model.deidentify(doc, metadata=metadata)
        assert deid.deidentified_text == want
