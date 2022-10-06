import unittest
from typing import Optional

import docdeid

from deduce import annotate
from deduce.annotate import tokenizer

from deduce.annotate import Person


class TestAnnotateMethods(unittest.TestCase):
    def _test_annotator(
        self,
        annotator: docdeid.BaseAnnotator,
        text: str,
        expected_annotations: set[docdeid.Annotation],
        metadata: Optional[dict] = None,
    ):

        document = docdeid.Document(
            text=text, tokenizers={'default': tokenizer}, metadata=metadata or {}
        )

        annotations = set(annotator.annotate(document))

        self.assertEqual(annotations, expected_annotations)

    def test_annotate_initial_with_capital(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotator = annotate._get_name_pattern_annotators()['initial_with_capital']

        metadata = {
            "patient": Person(
                first_names=['Jan'],
                surname='Jansen'
            )
        }

        expected_annotations = {
            docdeid.Annotation(
                text="J. Jansen", start_char=62, end_char=71, tag="initiaal+naam"
            ),
        }

        self._test_annotator(annotator, text, expected_annotations, metadata)

    def test_annotate_interfix(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotator = annotate._get_name_pattern_annotators()['interfix_with_name']

        metadata = {
            "patient": Person(
                first_names=['Jan'],
                surname='Jansen'
            )
        }

        expected_annotations = {
            docdeid.Annotation(
                text='de Visser', start_char=191, end_char=200, tag='interfix+naam'
            ),
        }

        self._test_annotator(annotator, text, expected_annotations, metadata)

    def test_annotate_prefix(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotator = annotate._get_name_pattern_annotators()['prefix_with_name']

        metadata = {
            "patient": Person(
                first_names=['Jan'],
                surname='Jansen'
            )
        }

        expected_annotations = {

            docdeid.Annotation(
                text='patient J', start_char=54, end_char=63, tag='prefix+naam'
            ),
        }

        self._test_annotator(annotator, text, expected_annotations, metadata)

    def test_annotate_person_surname(self):

        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotator = annotate._get_name_pattern_annotators()['person_surname']

        metadata = {
            "patient": Person(
                first_names=['Jan'],
                surname='Jansen'
            )
        }

        expected_annotations = {
            docdeid.Annotation(text='Jansen', start_char=65, end_char=71, tag='achternaam_patient'),
            docdeid.Annotation(text='Jansen', start_char=43, end_char=49, tag='achternaam_patient')

        }

        self._test_annotator(annotator, text, expected_annotations, metadata)

    def test_annotate_initials(self):

        text = "C. geeft aan dood te willen. C. tot op nu blij"
        annotator = annotate._get_name_pattern_annotators()['person_initials']

        metadata = {
            "patient": Person(
                first_names=['Peter', 'Charles'],
                surname='de Jong',
                initials='C',
                given_name='Charlie'
            )
        }

        expected_annotations = {
            docdeid.Annotation(
                text="C", start_char=29, end_char=30, tag="initialen_patient"
            ),
            docdeid.Annotation(text="C", start_char=0, end_char=1, tag="initialen_patient"),
        }

        self._test_annotator(annotator, text, expected_annotations, metadata)

    def test_annotate_initials_attached(self):

        text = "toegangstijd: N.v.t."
        annotator = annotate._get_name_pattern_annotators()['person_initial_from_name']

        metadata = {
            "patient": Person(
                first_names=['Nicholas', 'David'],
                surname='de Jong',
                initials='ND',
                given_name='Niek'
            )
        }

        expected_annotations = {
            docdeid.Annotation(text="N", start_char=14, end_char=15, tag="initiaal_patient")
        }

        self._test_annotator(annotator, text, expected_annotations, metadata)

    def test_annotate_address_no_number(self):

        text = "I live in Havikstraat since my childhood"
        annotator = annotate.get_doc_processors()['street_with_number']

        expected_annotations = {
            docdeid.Annotation(
                text="Havikstraat", start_char=10, end_char=21, tag="locatie"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_annotate_address_with_number(self):

        text = "I live in Havikstraat 43 since my childhood"
        annotator = annotate.get_doc_processors()['street_with_number']

        expected_annotations = {
            docdeid.Annotation(
                text="Havikstraat 43", start_char=10, end_char=24, tag="locatie"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_annotate_address_long_number(self):

        text = "I live in Havikstraat 4324598 since my childhood"
        annotator = annotate.get_doc_processors()['street_with_number']

        expected_annotations = {
            docdeid.Annotation(
                text="Havikstraat 4324598",
                start_char=10,
                end_char=29,
                tag="locatie",
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_preserve_institution_casing(self):

        text = "Ik ben in Altrecht geweest"
        annotator = annotate.get_doc_processors()['institution']

        expected_annotations = {
            docdeid.Annotation(
                text="Altrecht", start_char=10, end_char=18, tag="instelling"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_skip_mg(self):

        text = "<LOCATIE Hoofdstraat> is mooi. (br)Lithiumcarbonaat 1600mg. Nog een zin"
        annotator = annotate.get_doc_processors()['postal_code']

        expected_annotations = set()

        self._test_annotator(annotator, text, expected_annotations)

    def test_annotate_postcode(self):

        text = "Mijn postcode is 3500LX, toch?"
        annotator = annotate.get_doc_processors()['postal_code']

        expected_annotations = {
            docdeid.Annotation(
                text="3500LX", start_char=17, end_char=23, tag="locatie"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_keep_punctuation_after_date(self):

        text = "Medicatie actueel	26-10, OXAZEPAM"
        annotator = annotate.get_doc_processors()['date_1']

        expected_annotations = {
            docdeid.Annotation(
                text="26-10", start_char=18, end_char=23, tag="datum"
            )
        }

        self._test_annotator(annotator, text, expected_annotations)

    def test_two_dates_with_comma(self):

        text = "24 april, 1 mei: pt gaat geen constructief contact aan"
        annotator = annotate.get_doc_processors()['date_2']

        expected_annotations = {
            docdeid.Annotation(
                text="24 april", start_char=0, end_char=8, tag="datum"
            ),
            docdeid.Annotation(
                text="1 mei", start_char=10, end_char=15, tag="datum"
            ),
        }

        self._test_annotator(annotator, text, expected_annotations)


if __name__ == "__main__":
    unittest.main()
