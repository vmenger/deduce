from typing import Optional

import docdeid as dd

from deduce.doc_processors import get_doc_processors
from deduce.lookup_sets import get_lookup_sets
from deduce.tokenize import DeduceTokenizer

lookup_sets = get_lookup_sets()
tokenizer = DeduceTokenizer()

deduce_processors = get_doc_processors(lookup_sets, tokenizer)


def get_annotator(name: str) -> Optional[dd.process.Annotator]:
    processor = deduce_processors[name]

    if isinstance(processor, dd.process.Annotator):
        return processor

    return None


def annotate_text(text: str, annotators: list[dd.process.Annotator]) -> dd.AnnotationSet:
    doc = dd.Document(text, tokenizers={"default": tokenizer})

    for annotator in annotators:
        annotator.process(doc)

    return doc.annotations


class TestLookupAnnotators:
    def test_annotate_institution(self):

        text = "Reinaerde, Universitair Medisch Centrum Utrecht, UMCU, Diakonessenhuis"
        annotator = get_annotator("institution")

        expected_annotations = {
            dd.Annotation(text="Universitair Medisch Centrum Utrecht", start_char=11, end_char=47, tag=annotator.tag),
            dd.Annotation(text="Diakonessenhuis", start_char=55, end_char=70, tag=annotator.tag),
            dd.Annotation(text="Centrum", start_char=32, end_char=39, tag=annotator.tag),
            dd.Annotation(text="UMCU", start_char=49, end_char=53, tag=annotator.tag),
            dd.Annotation(text="Reinaerde", start_char=0, end_char=9, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_residence(self):

        text = "Nieuwerkerk aan den IJssel, Soesterberg, Broekhuizen"
        annotator = get_annotator("residence")

        expected_annotations = {
            dd.Annotation(text="Broekhuizen", start_char=41, end_char=52, tag=annotator.tag),
            dd.Annotation(text="Soesterberg", start_char=28, end_char=39, tag=annotator.tag),
            dd.Annotation(text="Nieuwerkerk aan den IJssel", start_char=0, end_char=26, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations


class TestRegexpAnnotators:
    def test_annotate_altrecht_regexp(self):

        text = "Altrecht Bipolair, altrecht Jong, Altrecht psychose"
        annotator = get_annotator("altrecht")
        expected_annotations = {
            dd.Annotation(text="Altrecht Bipolair", start_char=0, end_char=17, tag=annotator.tag),
            dd.Annotation(text="altrecht Jong", start_char=19, end_char=32, tag=annotator.tag),
            dd.Annotation(text="Altrecht", start_char=34, end_char=42, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_street_without_number(self):

        text = "I live in Havikstraat since my childhood"
        annotator = get_annotator("street_with_number")
        expected_annotations = {dd.Annotation(text="Havikstraat", start_char=10, end_char=21, tag=annotator.tag)}

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_address_with_number(self):

        text = "I live in Havikstraat 43 since my childhood"
        annotator = get_annotator("street_with_number")
        expected_annotations = {dd.Annotation(text="Havikstraat 43", start_char=10, end_char=24, tag="locatie")}

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_address_long_number(self):

        text = "I live in Havikstraat 4324598 since my childhood"
        annotator = get_annotator("street_with_number")
        expected_annotations = {
            dd.Annotation(
                text="Havikstraat 4324598",
                start_char=10,
                end_char=29,
                tag="locatie",
            )
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_postal_code(self):

        text = "1200ab, 1200mg, 1200MG, 1200AB"

        annotator = get_annotator("postal_code")
        expected_annotations = {
            dd.Annotation(text="1200AB", start_char=24, end_char=30, tag=annotator.tag),
            dd.Annotation(text="1200ab", start_char=0, end_char=6, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_postbus(self):

        text = "Postbus 12345, postbus 12345"

        annotator = get_annotator("postbus")
        expected_annotations = {
            dd.Annotation(text="Postbus 12345", start_char=0, end_char=13, tag=annotator.tag),
            dd.Annotation(text="postbus 12345", start_char=15, end_char=28, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_phone_number(self):

        text = "088-7555555, 088-1309670"

        annotator = [get_annotator("phone_1"), get_annotator("phone_1"), get_annotator("phone_1")]
        expected_annotations = {
            dd.Annotation(text="088-7555555", start_char=0, end_char=11, tag=annotator[0].tag),
            dd.Annotation(text="088-1309670", start_char=13, end_char=24, tag=annotator[0].tag),
        }

        annotations = annotate_text(text, annotator)

        assert annotations == expected_annotations

    def test_annotate_patient_number(self):

        text = "1348438, 458, 4584358"

        annotator = get_annotator("patient_number")
        expected_annotations = {
            dd.Annotation(text="4584358", start_char=14, end_char=21, tag=annotator.tag),
            dd.Annotation(text="1348438", start_char=0, end_char=7, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_date(self):

        text = "26-10, 24 april, 1 mei"

        annotator = [get_annotator("date_1"), get_annotator("date_2")]
        expected_annotations = {
            dd.Annotation(text="26-10", start_char=0, end_char=5, tag=annotator[0].tag),
            dd.Annotation(text="24 april", start_char=7, end_char=15, tag=annotator[0].tag),
            dd.Annotation(text="1 mei", start_char=17, end_char=22, tag=annotator[0].tag),
        }

        annotations = annotate_text(text, annotator)

        assert annotations == expected_annotations

    def test_annotate_age(self):

        text = "14 jaar oud, 14-jarige, 14 jarig"

        annotator = get_annotator("age")
        expected_annotations = {
            dd.Annotation(text="14", start_char=13, end_char=15, tag=annotator.tag),
            dd.Annotation(text="14", start_char=0, end_char=2, tag=annotator.tag),
            dd.Annotation(text="14", start_char=24, end_char=26, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_email(self):

        text = "email@voorbeeld.nl, jan_jansen@gmail.com, info@umcutrecht.nl"

        annotator = get_annotator("email")
        expected_annotations = {
            dd.Annotation(text="jan_jansen@gmail.com", start_char=20, end_char=40, tag=annotator.tag),
            dd.Annotation(text="email@voorbeeld.nl", start_char=0, end_char=18, tag=annotator.tag),
            dd.Annotation(text="info@umcutrecht.nl", start_char=42, end_char=60, tag=annotator.tag),
        }

        annotations = annotate_text(text, [annotator])

        assert annotations == expected_annotations

    def test_annotate_url(self):

        text = (
            "www.umcutrecht.nl, "
            "https://packaging.pypi.org, "
            "softwareengineering.stackexchange.com/questions/348295/is-there-such-a-thing-as-having-too-many-unit-tests"
        )

        annotator = [get_annotator("url_1"), get_annotator("url_2")]

        expected_annotations = {
            dd.Annotation(text="www.umcutrecht.nl", start_char=0, end_char=17, tag=annotator[0].tag),
            dd.Annotation(text="https://packaging.pypi.org", start_char=19, end_char=45, tag=annotator[0].tag),
            dd.Annotation(
                text="softwareengineering.stackexchange.com/questions/348295/"
                "is-there-such-a-thing-as-having-too-many-unit-tests",
                start_char=47,
                end_char=153,
                tag=annotator[0].tag,
            ),
        }

        annotations = annotate_text(text, annotator)

        assert annotations == expected_annotations
