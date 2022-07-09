import unittest

from deduce import annotate


class TestAnnotateMethods(unittest.TestCase):
    def test_annotate_names(self):
        text = (
            "Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            "(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            "oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )
        annotated_names = annotate.annotate_names(
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
        annotated_names = annotate.annotate_names_context(text)
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
        annotated_names = annotate.annotate_names_context(text)
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
        annotated_names = annotate.annotate_names_context(text)
        expected_text = (
            "Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Er is ook een andere <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez> hier"
        )
        self.assertEqual(expected_text, annotated_names)

    def test_simple_context(self):
        text = "V. <ACHTERNAAMONBEKEND Menger>"
        annotated_names = annotate.annotate_names_context(text)
        expected_text = "<INITIAAL V. <ACHTERNAAMONBEKEND Menger>>"
        self.assertEqual(expected_text, annotated_names)

    def test_coordinating_nexus(self):
        text = """We hebben o.a. gesproken om een verwijsbrief te verzorgen naar Ajax, <PREFIXNAAM PJ> en Pieter"""
        annotated_names = annotate.annotate_names_context(text)
        expected_text = """We hebben o.a. gesproken om een verwijsbrief te verzorgen naar Ajax, <MEERDEREPERSONEN <PREFIXNAAM PJ> en Pieter>"""
        self.assertEqual(expected_text, annotated_names)

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
        text = "Adalberto <ACHTERNAAMONBEKEND Koning> en Mariangela"
        annotated = annotate.annotate_names_context(text)
        expected_text = "<MEERDEREPERSONEN <INITIAAL Adalberto <ACHTERNAAMONBEKEND Koning>> en Mariangela>"
        self.assertEqual(expected_text, annotated)

    def test_preserve_institution_casing(self):
        text = "Ik ben in Altrecht geweest"
        annotated_institutions_text = annotate.annotate_institution(text)
        expected_text = "Ik ben in <INSTELLING Altrecht> geweest"
        self.assertEqual(expected_text, annotated_institutions_text)

    def test_skip_mg(self):
        text = "<LOCATIE Hoofdstraat> is mooi. (br)Lithiumcarbonaat 1600mg. Nog een zin"
        annotated_postcodes_text = annotate.annotate_postalcode(text)
        self.assertEqual(text, annotated_postcodes_text)

    def test_annotate_postcode(self):
        text = "Mijn postcode is 3500LX, toch?"
        annotated_postcodes_text = annotate.annotate_postalcode(text)
        expected_text = text.replace("3500LX", "<LOCATIE 3500LX>")
        self.assertEqual(expected_text, annotated_postcodes_text)

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
        annotated = [
            annotate.annotate_institution(text.replace("xxx", el[0])) for el in examples
        ]
        expected = [text.replace("xxx", el[1]) for el in examples]
        self.assertEqual(expected, annotated)

    def test_annotate_context_keep_initial(self):
        text = "Mijn naam is M <ACHTERNAAMONBEKEND Smid> de Vries"
        annotated_context_names = annotate.annotate_names_context(text)
        expected = "Mijn naam is <INTERFIXACHTERNAAM <INITIAAL M <ACHTERNAAMONBEKEND Smid>> de Vries>"
        self.assertEqual(expected, annotated_context_names)

    def test_keep_punctuation_after_date(self):
        text = "Medicatie actueel	26-10, OXAZEPAM"
        annotated_dates = annotate.annotate_date(text)
        expected = text.replace("26-10", "<DATUM 26-10>")
        self.assertEqual(expected, annotated_dates)

    def test_two_dates_with_comma(self):
        text = "24 april, 1 mei: pt gaat geen constructief contact aan"
        annotated_dates = annotate.annotate_date(text)
        expected = (
            "<DATUM 24 april>, <DATUM 1 mei>: pt gaat geen constructief contact aan"
        )
        self.assertEqual(expected, annotated_dates)


if __name__ == "__main__":
    unittest.main()
