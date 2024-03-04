import pytest

import docdeid as dd
from deduce import Deduce

from deduce.person import Person

text = (
    "betreft: Jan Jansen, bsn 111222333, patnr 000334433. De patient J. Jansen is 64 "
    "jaar oud en woonachtig in Utrecht, IJSWEG 10r. Hij werd op 10 oktober 2018 door arts "
    "Peter de Visser ontslagen van de kliniek van het UMCU. Voor nazorg kan hij "
    "worden bereikt via j.JNSEN.123@gmail.com of (06)12345678."
)


@pytest.fixture
def model(shared_datadir):
    return Deduce(save_lookup_structs=False,
                  lookup_data_path=shared_datadir / "lookup")


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
                dd.Annotation(
                    text="J. Jansen", start_char=64, end_char=73, tag="patient"
                ),
                dd.Annotation(
                    text="Jan Jansen", start_char=9, end_char=19, tag="patient"
                ),
                dd.Annotation(
                    text="10 oktober 2018", start_char=139, end_char=154, tag="datum"
                ),
                dd.Annotation(text="64", start_char=77, end_char=79, tag="leeftijd"),
                dd.Annotation(text="000334433", start_char=42, end_char=51, tag="id"),
                dd.Annotation(
                    text="Utrecht", start_char=106, end_char=113, tag="locatie"
                ),
                dd.Annotation(
                    text="IJSWEG 10r", start_char=115, end_char=125, tag="locatie"
                ),
                dd.Annotation(
                    text="UMCU", start_char=214, end_char=218, tag="ziekenhuis"
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
            "</LOCATIE>, <LOCATIE>IJSWEG 10r</LOCATIE>. Hij werd op <DATUM>10 "
            "oktober 2018</DATUM> door arts <PERSOON>Peter de "
            "Visser</PERSOON> ontslagen van de kliniek van het "
            "<ZIEKENHUIS>UMCU</ZIEKENHUIS>. Voor nazorg kan hij worden "
            "bereikt via <EMAILADRES>j.JNSEN.123@gmail.com</EMAILADRES> of "
            "<TELEFOONNUMMER>(06)12345678</TELEFOONNUMMER>."
        )

        assert dd.utils.annotate_intext(doc) == expected_intext_annotated
