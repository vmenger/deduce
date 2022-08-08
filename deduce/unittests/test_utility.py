import unittest

import docdeid

from deduce import utility


class TestUtilityMethods(unittest.TestCase):
    def test_parse_tag(self):
        tag = "<VOORNAAMONBEKEND Peter>"
        tag_type, text = utility.parse_tag(tag)
        self.assertEqual("VOORNAAMONBEKEND", tag_type)
        self.assertEqual("Peter", text)

    def test_find_name_tags(self):
        annotated_text = (
            "Dit is stukje tekst met daarin de naam <VOORNAAMPAT Jan> <ACHTERNAAMPAT Jansen>. De "
            "<PREFIXNAAM patient J>. <ACHTERNAAMPAT Jansen> (e: j.jnsen@email.com, t: 06-12345678) is 64 "
            "jaar oud en woonachtig in Utrecht. Hij werd op 10 oktober door arts <VOORNAAMONBEKEND "
            "Peter> <INTERFIXNAAM de Visser> ontslagen van de kliniek van het UMCU."
        )
        found_tags = utility.find_tags(annotated_text)
        expected_tags = [
            "<VOORNAAMPAT Jan>",
            "<ACHTERNAAMPAT Jansen>",
            "<PREFIXNAAM patient J>",
            "<ACHTERNAAMPAT Jansen>",
            "<VOORNAAMONBEKEND Peter>",
            "<INTERFIXNAAM de Visser>",
        ]
        self.assertEqual(expected_tags, found_tags)

    def test_get_annotations(self):
        text = (
            "Dit is stukje tekst met daarin de naam <VOORNAAMPAT Jan> <ACHTERNAAMPAT Jansen>. De "
            "<PREFIXNAAM patient J>. <ACHTERNAAMPAT Jansen> (e: j.jnsen@email.com, t: 06-12345678) is 64 "
            "jaar oud en woonachtig in Utrecht. Hij werd op 10 oktober door arts <VOORNAAMONBEKEND "
            "Peter> <INTERFIXNAAM de Visser> ontslagen van de kliniek van het UMCU."
        )
        tags = [
            "<VOORNAAMPAT Jan>",
            "<ACHTERNAAMPAT Jansen>",
            "<PREFIXNAAM patient J>",
            "<ACHTERNAAMPAT Jansen>",
            "<VOORNAAMONBEKEND Peter>",
            "<INTERFIXNAAM de Visser>",
        ]
        expected_annotations = [
            docdeid.Annotation("Jan", 39, 42, "VOORNAAMPAT"),
            docdeid.Annotation("Jansen", 43, 49, "ACHTERNAAMPAT"),
            docdeid.Annotation("patient J", 54, 63, "PREFIXNAAM"),
            docdeid.Annotation("Jansen", 65, 71, "ACHTERNAAMPAT"),
            docdeid.Annotation("Peter", 185, 190, "VOORNAAMONBEKEND"),
            docdeid.Annotation("de Visser", 191, 200, "INTERFIXNAAM"),
        ]
        found_annotations = utility.get_annotations(text, tags)
        self.assertEqual(expected_annotations, found_annotations)

    def test_annotate_text(self):
        annotated_text = (
            "Dit is stukje tekst met daarin de naam <PATIENT Jan Jansen>. De "
            "<PATIENT patient J. Jansen> (e: <URL j.jnsen@email.com>, t: <TELEFOONNUMMER 06-12345678>) "
            "is <LEEFTIJD 64> jaar oud en woonachtig in <LOCATIE Utrecht>. Hij werd op "
            "<DATUM 10 oktober> door arts <PERSOON Peter de Visser> ontslagen van de kliniek van het "
            "<INSTELLING umcu>."
        )

        tags = utility.find_tags(annotated_text)
        annotations = utility.get_annotations(annotated_text, tags)
        expected_annotations = [
            docdeid.Annotation("Jan Jansen", 39, 49, "PATIENT"),
            docdeid.Annotation("patient J. Jansen", 54, 71, "PATIENT"),
            docdeid.Annotation("j.jnsen@email.com", 76, 93, "URL"),
            docdeid.Annotation("06-12345678", 98, 109, "TELEFOONNUMMER"),
            docdeid.Annotation("64", 114, 116, "LEEFTIJD"),
            docdeid.Annotation("Utrecht", 143, 150, "LOCATIE"),
            docdeid.Annotation("10 oktober", 164, 174, "DATUM"),
            docdeid.Annotation("Peter de Visser", 185, 200, "PERSOON"),
            docdeid.Annotation("umcu", 234, 238, "INSTELLING"),
        ]
        self.assertEqual(expected_annotations, annotations)

    def test_get_annotations_leading_space(self):
        annotated_text = "Overleg gehad met <PERSOON Jan Jansen>"
        tags = ["<PERSOON Jan Jansen>"]
        annotations = utility.get_annotations(annotated_text, tags, 1)
        self.assertEqual(1, len(annotations))
        self.assertEqual(19, annotations[0].start_char)

    def test_get_first_non_whitespace(self):
        self.assertEqual(1, utility.get_first_non_whitespace(" Overleg"))

    def test_flatten_text_all_phi(self):
        text = "<INSTELLING UMC <LOCATIE Utrecht>>"
        flattened = utility.flatten_text_all_phi(text)
        self.assertEqual("<INSTELLING UMC Utrecht>", flattened)

    def test_flatten_text_all_phi_no_nested(self):
        text = "<PERSOON Peter> came today and said he loved the <INSTELLING UMC>"
        flattened = utility.flatten_text_all_phi(text)
        self.assertEqual(text, flattened)

    def test_flatten_text_all_phi_extra_flat(self):
        text = "<INSTELLING UMC <LOCATIE Utrecht>> is the best hospital in <LOCATIE Utrecht>"
        flattened = utility.flatten_text_all_phi(text)
        self.assertEqual(
            "<INSTELLING UMC Utrecht> is the best hospital in <LOCATIE Utrecht>",
            flattened,
        )

    def test_flatten_text_all_phi_extra_nested(self):
        text = "<INSTELLING UMC <LOCATIE Utrecht>> was founded by <PERSOON Jan van <LOCATIE Apeldoorn>>"
        flattened = utility.flatten_text_all_phi(text)
        self.assertEqual(
            "<INSTELLING UMC Utrecht> was founded by <PERSOON Jan van Apeldoorn>",
            flattened,
        )


if __name__ == "__main__":
    unittest.main()
