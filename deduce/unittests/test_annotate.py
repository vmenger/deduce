import unittest

import docdeid

from deduce import annotate
from deduce.annotate import tokenizer

from typing import Optional


class TestAnnotateMethods(unittest.TestCase):

    def _test_annotator(self, annotator: docdeid.BaseAnnotator, text: str, expected_annotations: set[docdeid.Annotation], meta_data: Optional[dict] = None):

        document = docdeid.Document(text=text, tokenizer=tokenizer, meta_data=meta_data or {})
        annotator.annotate(document)

        self.assertEqual(document.annotations, expected_annotations)

    def test_annotate_names(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotator = annotate.NamesAnnotator()

        meta_data = {
            'patient_first_names': "Jan",
            'patient_surname': "Jansen",
            'patient_initial': "",
            'patient_given_name': "",
        }

        expected_annotations = {
            docdeid.Annotation(text='J. Jansen', start_char=62, end_char=71, category='PATIENT'),
            docdeid.Annotation(text='Peter de Visser', start_char=185, end_char=200, category='PERSOON'),
            docdeid.Annotation(text='patient ', start_char=54, end_char=62, category='PERSOON'),
            docdeid.Annotation(text='Jan Jansen', start_char=39, end_char=49, category='PATIENT')
        }

        self._test_annotator(annotator, text, expected_annotations, meta_data)

    def test_annotate_initials(self):

        text = "C. geeft aan dood te willen. C. tot op nu blij"
        annotator = annotate.NamesAnnotator()

        meta_data = {
            'patient_first_names': "Peter Charles",
            'patient_surname': "de Jong",
            'patient_initial': "PC",
            'patient_given_name': "Charlie",
        }

        expected_annotations = {
            docdeid.Annotation(text='C', start_char=29, end_char=30, category='PATIENT'),
            docdeid.Annotation(text='C', start_char=0, end_char=1, category='PATIENT')
        }

        self._test_annotator(annotator, text, expected_annotations, meta_data)

    def test_annotate_initials_attached(self):

        text = "toegangstijd: N.v.t."
        annotator = annotate.NamesAnnotator()

        meta_data = {
            'patient_first_names': "Nicholas David",
            'patient_initials': "ND",
            'patient_surname': "de Jong",
            'patient_given_name': "Niek",
        }

        expected_annotations = {
            docdeid.Annotation(text='N', start_char=14, end_char=15, category='PATIENT')
        }

        self._test_annotator(annotator, text, expected_annotations, meta_data)

    def test_annotate_address_no_number(self):

        text = "I live in Havikstraat since my childhood"
        annotator = annotate.AddressAnnotator()

        expected_annotations = {
            docdeid.Annotation(
                text="Havikstraat", start_char=10, end_char=21, category="LOCATIE"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_annotate_address_with_number(self):

        text = "I live in Havikstraat 43 since my childhood"
        annotator = annotate.AddressAnnotator()

        expected_annotations = {
            docdeid.Annotation(
                text="Havikstraat 43", start_char=10, end_char=24, category="LOCATIE"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_annotate_address_long_number(self):

        text = "I live in Havikstraat 4324598 since my childhood"
        annotator = annotate.AddressAnnotator()

        expected_annotations = {
            docdeid.Annotation(
                text="Havikstraat 4324598",
                start_char=10,
                end_char=29,
                category="LOCATIE",
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_preserve_institution_casing(self):

        text = "Ik ben in Altrecht geweest"
        annotator = annotate.InstitutionAnnotator()

        expected_annotations = {
            docdeid.Annotation(
                text="Altrecht", start_char=10, end_char=18, category="INSTELLING"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_skip_mg(self):

        text = "<LOCATIE Hoofdstraat> is mooi. (br)Lithiumcarbonaat 1600mg. Nog een zin"
        annotator = annotate.PostalcodeAnnotator()

        expected_annotations = set()

        self._test_annotator(annotator, text, expected_annotations)

    def test_annotate_postcode(self):

        text = "Mijn postcode is 3500LX, toch?"
        annotator = annotate.PostalcodeAnnotator()

        expected_annotations = {
            docdeid.Annotation(
                text="3500LX", start_char=17, end_char=23, category="LOCATIE"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_keep_punctuation_after_date(self):

        text = "Medicatie actueel	26-10, OXAZEPAM"
        annotator = annotate.DateAnnotator()

        expected_annotations = {
            docdeid.Annotation(
                text="26-10", start_char=18, end_char=23, category="DATUM"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_two_dates_with_comma(self):

        text = "24 april, 1 mei: pt gaat geen constructief contact aan"
        annotator = annotate.DateAnnotator()

        expected_annotations = {
            docdeid.Annotation(
                text="24 april", start_char=0, end_char=8, category="DATUM"
            ),
            docdeid.Annotation(
                text="1 mei", start_char=10, end_char=15, category="DATUM"
            ),
        }

        self._test_annotator(annotator, text, expected_annotations)


if __name__ == "__main__":
    unittest.main()
