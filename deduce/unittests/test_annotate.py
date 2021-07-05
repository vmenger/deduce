import unittest

from deduce import annotate


class TestAnnotateMethods(unittest.TestCase):
    def test_annotate_names(self):
        text = u"Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen " \
               u"(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 " \
               u"oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        annotated_names = annotate.annotate_names(text, patient_first_names="Jan", patient_surname="Jansen",
                                                  patient_initial="", patient_given_name="")
        expected_text = "Dit is stukje tekst met daarin de naam <VOORNAAMPAT Jan> <ACHTERNAAMPAT Jansen>. De " \
                        "<PREFIXNAAM patient J>. <ACHTERNAAMPAT Jansen> (e: j.jnsen@email.com, t: 06-12345678) is 64 " \
                        "jaar oud en woonachtig in Utrecht. Hij werd op 10 oktober door arts <VOORNAAMONBEKEND " \
                        "Peter> <INTERFIXNAAM de Visser> ontslagen van de kliniek van het UMCU."
        self.assertEqual(expected_text, annotated_names)

    def test_duplicated_names(self):
        text = 'Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, ' \
               '<VOORNAAMONBEKEND Peter> van Gonzalez'
        annotated_names = annotate.annotate_names_context(text)
        expected_text = 'Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. ' \
                        'Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>'
        self.assertEqual(expected_text, annotated_names)


    def test_duplicated_names_longer(self):
        text = 'Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, ' \
               '<VOORNAAMONBEKEND Peter> van Gonzalez. Er is ook een Pieter de Visser hier'
        annotated_names = annotate.annotate_names_context(text)
        expected_text = 'Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. ' \
                        'Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. ' \
                        'Er is ook een Pieter de Visser hier'
        self.assertEqual(expected_text, annotated_names)


    def test_duplicated_names_triple(self):
        text = 'Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, ' \
               '<VOORNAAMONBEKEND Peter> van Gonzalez. Er is ook een andere <VOORNAAMONBEKEND Peter> van Gonzalez hier'
        annotated_names = annotate.annotate_names_context(text)
        expected_text = 'Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. ' \
                        'Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. ' \
                        'Er is ook een andere <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez> hier'
        self.assertEqual(expected_text, annotated_names)

if __name__ == "__main__":
    unittest.main()
