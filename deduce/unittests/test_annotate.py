import unittest
from deduce.annotate import annotate_names, replace_altrecht_annotations
from deduce.utilcls import Annotation
from deduce import annotate


class TestAnnotateMethods(unittest.TestCase):
    def test_annotate_names_context(self):
        result = annotate.annotate_names_context("Peter Parker", [])
        self.assertEqual(list, type(result))

    def test_insert_annotations(self):
        text = "Jan Jansen en Pieter van Duinen kwamen"
        annotations = [Annotation(0, 10, "PERSOON", "Jan Jansen"),
                       Annotation(14, 31, "PATIENT", "Pieter van Duinen")]
        expected_text = "<PERSOON Jan Jansen> en <PATIENT Pieter van Duinen> kwamen"
        retrieved_text = annotate.insert_annotations(text, annotations)
        self.assertEqual(expected_text, retrieved_text)

    def test_annotate_names(self):
        annotations = annotate_names("Peter  Parker", "Peter", "P.", "Parker", "Pete")
        expected_annotations = [Annotation(0, 5, "VOORNAAMPAT", "Peter"),
                                Annotation(7, 13, "ACHTERNAAMPAT", "Parker")]
        self.assertEqual(2, len(expected_annotations))
        self.assertEqual(expected_annotations, annotations)

    def test_remove_annotations_in_range(self):
        annotations = [Annotation(0, 10, "PERSOON", "Jan Jansen"),
                       Annotation(14, 31, "PATIENT", "Pieter van Duinen")]
        retrieved_annotations = annotate.remove_annotations_in_range(annotations, 14, 31)
        self.assertEqual([annotations[0]], retrieved_annotations)

    def test_duplicated_names(self):
        text = 'Dank je Peter van Gonzalez. Met vriendelijke groet, Peter van Gonzalez'
        old_annotations = [Annotation(8, 13, 'VOORNAAMONBEKEND', 'Peter'),
                           Annotation(52, 57, 'VOORNAAMONBEKEND', 'Peter')]
        annotated_names = annotate.annotate_names_context(text, old_annotations)
        expected_annotations = [Annotation(8, 26, 'INTERFIXACHTERNAAMVOORNAAMONBEKEND', 'Peter van Gonzalez'),
                                Annotation(52, 70, 'INTERFIXACHTERNAAMVOORNAAMONBEKEND', 'Peter van Gonzalez')]
        self.assertEqual(expected_annotations, annotated_names)

    def test_duplicated_names_longer(self):
        text = 'Dank je Peter van Gonzalez. Met vriendelijke groet, Peter van Gonzalez. ' + \
               'Er is ook een Pieter de Visser hier'
        old_annotations = [Annotation(8, 13, 'VOORNAAMONBEKEND', 'Peter'),
                           Annotation(52, 57, 'VOORNAAMONBEKEND', 'Peter')]
        annotated_names = annotate.annotate_names_context(text, old_annotations)
        expected_annotations = [Annotation(8, 26, 'INTERFIXACHTERNAAMVOORNAAMONBEKEND', 'Peter van Gonzalez'),
                                Annotation(52, 70, 'INTERFIXACHTERNAAMVOORNAAMONBEKEND', 'Peter van Gonzalez')]
        self.assertEqual(expected_annotations, annotated_names)

    def test_duplicated_names_triple(self):
        text = 'Dank je Peter van Gonzalez. Met vriendelijke groet, Peter van Gonzalez. ' + \
               'Er is ook een andere Peter van Gonzalez hier'
        old_annotations = [Annotation(8, 13, 'VOORNAAMONBEKEND', 'Peter'),
                           Annotation(52, 57, 'VOORNAAMONBEKEND', 'Peter'),
                           Annotation(93, 98, 'VOORNAAMONBEKEND', 'Peter')]
        annotated_names = annotate.annotate_names_context(text, old_annotations)
        expected_annotations = [Annotation(8, 26, 'INTERFIXACHTERNAAMVOORNAAMONBEKEND', 'Peter van Gonzalez'),
                                Annotation(52, 70, 'INTERFIXACHTERNAAMVOORNAAMONBEKEND', 'Peter van Gonzalez'),
                                Annotation(93, 111, 'INTERFIXACHTERNAAMVOORNAAMONBEKEND', 'Peter van Gonzalez')]
        self.assertEqual(expected_annotations, annotated_names)

    def test_simple_context(self):
        text = "V. Menger"
        old_annotations = [Annotation(3, 9, 'ACHTERNAAMONBEKEND', 'Menger')]
        annotated_names = annotate.annotate_names_context(text, old_annotations)
        expected_annotations = [Annotation(0, 9, 'INITIAALACHTERNAAMONBEKEND', 'V. Menger')]
        self.assertEqual(expected_annotations, annotated_names)

    def test_coordinating_nexus(self):
        text = 'We hebben o.a. gesproken om een verwijsbrief te verzorgen naar Ajax, PJ en Pieter'
        old_annotations = [Annotation(69, 71, 'PREFIXNAAM', 'PJ')]
        annotated_names = annotate.annotate_names_context(text, old_annotations)
        expected_annotations = [Annotation(69, 81, 'MEERDEREPERSONENPREFIXNAAM', 'PJ en Pieter')]
        self.assertEqual(expected_annotations, annotated_names)

    def test_annotate_initials(self):
        text = "C. geeft aan dood te willen. C. tot op nu blij"
        annotated_names = annotate.annotate_names(
            text,
            patient_first_names="Peter Charles",
            patient_surname="de Jong",
            patient_initial="PC",
            patient_given_name="Charlie",
        )
        expected_text = (
            "<INITIAALPAT C.> geeft aan dood te willen. <INITIAALPAT C.> tot op nu blij"
        )
        self.assertEqual(expected_text, annotated_names)

    def test_annotate_initials_attached(self):
        text = "Toegangstijd: N.v.t."
        patient_first_names = "Nicholas David"
        patient_initials = "ND"
        patient_surname = "de Jong"
        patient_given_name = "Niek"
        annotated_names = annotate.annotate_names(
            text,
            patient_first_names=patient_first_names,
            patient_surname=patient_surname,
            patient_initial=patient_initials,
            patient_given_name=patient_given_name,
        )
        expected_text = "Toegangstijd: <INITIAALPAT N.>v.t."
        self.assertEqual(expected_text, annotated_names)

    def test_annotate_address_no_number(self):
        text = "I live in Havikstraat since my childhood"
        address = annotate.annotate_address(text)
        self.assertEqual("I live in <LOCATIE Havikstraat> since my childhood", address)

    def test_annotate_address_with_number(self):
        text = "I live in Havikstraat 43 since my childhood"
        address = annotate.annotate_address(text)
        self.assertEqual(
            "I live in <LOCATIE Havikstraat 43> since my childhood", address
        )

    def test_annotate_address_long_number(self):
        text = "I live in Havikstraat 4324598 since my childhood"
        address = annotate.annotate_address(text)
        self.assertEqual(
            "I live in <LOCATIE Havikstraat 4324598> since my childhood", address
        )

    def test_coordinating_nexus_with_preceding_name(self):
        text = 'Adalberto Koning en Mariangela'
        old_annotations = [Annotation(10, 16, 'ACHTERNAAMONBEKEND', 'Koning')]
        annotated = annotate.annotate_names_context(text, old_annotations)
        expected_annotations = [Annotation(0, len(text), 'MEERDEREPERSONENINITIAALACHTERNAAMONBEKEND', text)]
        self.assertEqual(expected_annotations, annotated)

    def test_preserve_institution_casing(self):
        text = 'Ik ben in Altrecht geweest'
        annotated_institutions_text = annotate.annotate_institution(text)
        expected_annotations = [Annotation(10, 18, 'INSTELLING', 'Altrecht')]
        self.assertEqual(expected_annotations, annotated_institutions_text)

    def test_skip_mg(self):
        text = '<LOCATIE Hoofdstraat> is mooi. (br)Lithiumcarbonaat 1600mg. Nog een zin'
        annotated_postcodes_text = annotate.annotate_postalcode(text)
        self.assertEqual(text, annotated_postcodes_text)

    def test_annotate_postcode(self):
        text = 'Mijn postcode is 3500LX, toch?'
        annotated_postcodes_text = annotate.annotate_postalcode(text)
        expected_text = text.replace('3500LX', '<LOCATIE 3500LX>')
        self.assertEqual(expected_text, annotated_postcodes_text)

    def test_annotate_altrecht(self):
        text = 'Opname bij xxx afgerond'
        examples = [('altrecht lunetten', 'altrecht'),
                    ('altrecht Lunetten', 'altrecht Lunetten'),
                    ('Altrecht lunetten', 'Altrecht'),
                    ('Altrecht Lunetten', 'Altrecht Lunetten'),
                    ('Altrecht Willem Arntszhuis', 'Altrecht Willem Arntszhuis'),
                    ('Altrecht Lunetten ziekenhuis', 'Altrecht Lunetten'),
                    ('ALtrecht Lunetten', 'ALtrecht Lunetten')]
        annotated = [annotate.annotate_institution(text.replace('xxx', el[0])) for el in examples]
        expected = [[Annotation(text.index('xxx'), text.index('xxx') + len(el[1]), 'INSTELLING', el[1])] \
                    for el in examples]
        print(1)
        self.assertListEqual(expected, annotated)

    def test_annotate_context_keep_initial(self):
        text = 'Mijn naam is M Smid de Vries'
        old_annotations = [Annotation(15, 19, 'ACHTERNAAMONBEKEND', 'Smid')]
        annotated_context_names = annotate.annotate_names_context(text, old_annotations)
        expected_annotations = [Annotation(13, 28, 'INTERFIXACHTERNAAMINITIAALACHTERNAAMONBEKEND', 'M Smid de Vries')]
        self.assertEqual(expected_annotations, annotated_context_names)

    def test_keep_punctuation_after_date(self):
        text = 'Medicatie actueel	26-10, OXAZEPAM'
        annotated_dates = annotate.annotate_date(text)
        expected = text.replace('26-10', '<DATUM 26-10>')
        self.assertEqual(expected, annotated_dates)

    def test_two_dates_with_comma(self):
        text = '24 april, 1 mei: pt gaat geen constructief contact aan'
        annotated_dates = annotate.annotate_date(text)
        expected = '<DATUM 24 april>, <DATUM 1 mei>: pt gaat geen constructief contact aan'
        self.assertEqual(expected, annotated_dates)

    def test_replace_altrecht_annotations(self):
        text = 'Opname bij Altrecht Utrecht'
        previous_annotations = [Annotation(11, 19, 'INSTELLING', 'Altrecht')]
        modified_annotations = replace_altrecht_annotations(text, previous_annotations)
        expected_annotations = [Annotation(11, 27, 'INSTELLING', 'Altrecht Utrecht')]
        self.assertEqual(expected_annotations, modified_annotations)

if __name__ == "__main__":
    unittest.main()
