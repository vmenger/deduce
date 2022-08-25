import unittest

import docdeid

from deduce import annotate


class TestAnnotateMethods(unittest.TestCase):
    def test_annotate_names(self):
        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )

        annotator = annotate.NamesAnnotator()

        annotated_names = annotator.annotate_intext(
            text,
            patient_first_names="Jan",
            patient_surname="Jansen",
            patient_initial="",
            patient_given_name="",
        )
        expected_text = (
            "Dit is stukje tekst met daarin de naam <VOORNAAMPAT Jan> <ACHTERNAAMPAT Jansen>. De "
            "<PREFIXNAAM patient J>. <ACHTERNAAMPAT Jansen> (e: j.jnsen@email.com, t: 06-12345678) is 64 "
            "jaar oud en woonachtig in Utrecht. Hij werd op 10 oktober door arts <VOORNAAMONBEKEND "
            "Peter> <INTERFIXNAAM de Visser> ontslagen van de kliniek van het UMCU."
        )
        self.assertEqual(expected_text, annotated_names)

    def test_duplicated_names(self):
        text = (
            "Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, "
            "<VOORNAAMONBEKEND Peter> van Gonzalez"
        )
        annotator = annotate.NamesAnnotator()
        annotated_names = annotator.annotate_names_context(text)
        expected_text = (
            "Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>"
        )
        self.assertEqual(expected_text, annotated_names)

    def test_duplicated_names_longer(self):
        text = (
            "Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, "
            "<VOORNAAMONBEKEND Peter> van Gonzalez. Er is ook een Pieter de Visser hier"
        )
        annotator = annotate.NamesAnnotator()
        annotated_names = annotator.annotate_names_context(text)
        expected_text = (
            "Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Er is ook een Pieter de Visser hier"
        )
        self.assertEqual(expected_text, annotated_names)

    def test_duplicated_names_triple(self):
        text = (
            "Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, "
            "<VOORNAAMONBEKEND Peter> van Gonzalez. Er is ook een andere <VOORNAAMONBEKEND Peter> van Gonzalez hier"
        )
        annotator = annotate.NamesAnnotator()
        annotated_names = annotator.annotate_names_context(text)
        expected_text = (
            "Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Er is ook een andere <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez> hier"
        )
        self.assertEqual(expected_text, annotated_names)

    def test_simple_context(self):
        text = "V. <ACHTERNAAMONBEKEND Menger>"
        annotator = annotate.NamesAnnotator()
        annotated_names = annotator.annotate_names_context(text)
        expected_text = "<INITIAAL V. <ACHTERNAAMONBEKEND Menger>>"
        self.assertEqual(expected_text, annotated_names)

    def test_coordinating_nexus(self):
        text = """We hebben o.a. gesproken om een verwijsbrief te verzorgen naar Ajax, <PREFIXNAAM PJ> en Pieter"""
        annotator = annotate.NamesAnnotator()
        annotated_names = annotator.annotate_names_context(text)

        expected_text = (
            """We hebben o.a. gesproken om een verwijsbrief te verzorgen naar Ajax, """
            """<MEERDEREPERSONEN <PREFIXNAAM PJ> en Pieter>"""
        )

        self.assertEqual(expected_text, annotated_names)

    def test_annotate_initials(self):
        text = "C. geeft aan dood te willen. C. tot op nu blij"

        annotator = annotate.NamesAnnotator()

        annotated_names = annotator.annotate_intext(
            text=text,
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

        annotator = annotate.NamesAnnotator()
        annotated_names = annotator.annotate_names(
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

        doc = docdeid.Document(text=text)
        annotate.AddressAnnotator().annotate(doc)

        expected = {
            docdeid.Annotation(text='Havikstraat', start_char=10, end_char=21, category='LOCATIE')
        }

        self.assertEqual(
            expected, doc.annotations
        )

    def test_annotate_address_with_number(self):

        text = "I live in Havikstraat 43 since my childhood"

        doc = docdeid.Document(text=text)
        annotate.AddressAnnotator().annotate(doc)

        expected = {
            docdeid.Annotation(text='Havikstraat 43', start_char=10, end_char=24, category='LOCATIE')
        }

        self.assertEqual(
            expected, doc.annotations
        )

    def test_annotate_address_long_number(self):

        text = "I live in Havikstraat 4324598 since my childhood"

        doc = docdeid.Document(text=text)
        annotate.AddressAnnotator().annotate(doc)

        expected = {
            docdeid.Annotation(text='Havikstraat 4324598', start_char=10, end_char=29, category='LOCATIE')
        }

        self.assertEqual(
            expected, doc.annotations
        )

    def test_coordinating_nexus_with_preceding_name(self):
        text = "Adalberto <ACHTERNAAMONBEKEND Koning> en Mariangela"
        annotator = annotate.NamesAnnotator()
        annotated = annotator.annotate_names_context(text)
        expected_text = "<MEERDEREPERSONEN <INITIAAL Adalberto <ACHTERNAAMONBEKEND Koning>> en Mariangela>"
        self.assertEqual(expected_text, annotated)

    def test_preserve_institution_casing(self):
        text = "Ik ben in Altrecht geweest"
        annotator = annotate.InstitutionAnnotator()
        annotated_institutions_text = annotator.annotate_intext(text)
        expected_text = "Ik ben in <INSTELLING Altrecht> geweest"
        self.assertEqual(expected_text, annotated_institutions_text)

    def test_skip_mg(self):

        text = "<LOCATIE Hoofdstraat> is mooi. (br)Lithiumcarbonaat 1600mg. Nog een zin"

        doc = docdeid.Document(text=text)
        annotate.PostalcodeAnnotator().annotate(doc)

        expected = set()

        self.assertEqual(expected, doc.annotations)

    def test_annotate_postcode(self):

        text = "Mijn postcode is 3500LX, toch?"

        doc = docdeid.Document(text=text)
        annotate.PostalcodeAnnotator().annotate(doc)

        expected = {
            docdeid.Annotation(
                text="3500LX", start_char=17, end_char=23, category="LOCATIE"
            )
        }

        self.assertEqual(expected, doc.annotations)

    def test_annotate_altrecht(self):
        text = "Opname bij xxx afgerond"
        examples = [
            ("altrecht lunetten", "<INSTELLING altrecht> lunetten"),
            ("altrecht Lunetten", "<INSTELLING altrecht Lunetten>"),
            ("Altrecht lunetten", "<INSTELLING Altrecht> lunetten"),
            ("Altrecht Lunetten", "<INSTELLING Altrecht Lunetten>"),
            ("Altrecht Willem Arntszhuis", "<INSTELLING Altrecht Willem Arntszhuis>"),
            (
                "Altrecht Lunetten ziekenhuis",
                "<INSTELLING Altrecht Lunetten> ziekenhuis",
            ),
            ("ALtrecht Lunetten", "<INSTELLING ALtrecht Lunetten>"),
        ]
        annotator = annotate.InstitutionAnnotator()
        annotated = [
            annotator.annotate_intext(text.replace("xxx", el[0])) for el in examples
        ]
        expected = [text.replace("xxx", el[1]) for el in examples]
        self.assertEqual(expected, annotated)

    def test_annotate_context_keep_initial(self):
        text = "Mijn naam is M <ACHTERNAAMONBEKEND Smid> de Vries"
        annotator = annotate.NamesAnnotator()
        annotated_context_names = annotator.annotate_names_context(text)
        expected = "Mijn naam is <INTERFIXACHTERNAAM <INITIAAL M <ACHTERNAAMONBEKEND Smid>> de Vries>"
        self.assertEqual(expected, annotated_context_names)

    def test_keep_punctuation_after_date(self):

        text = "Medicatie actueel	26-10, OXAZEPAM"
        doc = docdeid.Document(text=text)
        annotate.DateAnnotator().annotate(doc)

        expected = {
            docdeid.Annotation(
                text="26-10", start_char=18, end_char=23, category="DATUM"
            )
        }

        self.assertEqual(expected, doc.annotations)

    def test_two_dates_with_comma(self):

        text = "24 april, 1 mei: pt gaat geen constructief contact aan"

        doc = docdeid.Document(text=text)
        annotate.DateAnnotator().annotate(doc)

        expected = {
            docdeid.Annotation(
                text="24 april", start_char=0, end_char=8, category="DATUM"
            ),
            docdeid.Annotation(
                text="1 mei", start_char=10, end_char=15, category="DATUM"
            ),
        }

        self.assertEqual(expected, doc.annotations)


if __name__ == "__main__":
    unittest.main()
