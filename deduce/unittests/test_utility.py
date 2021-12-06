import codecs
import unittest
from unittest.mock import patch

from deduce import utility
from deduce.tokenizer import tokenize
from deduce.utilcls import Token, TokenGroup, Annotation


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
            Annotation(39, 42, "VOORNAAMPAT", "Jan"),
            Annotation(43, 49, "ACHTERNAAMPAT", "Jansen"),
            Annotation(54, 63, "PREFIXNAAM", "patient J"),
            Annotation(65, 71, "ACHTERNAAMPAT", "Jansen"),
            Annotation(185, 190, "VOORNAAMONBEKEND", "Peter"),
            Annotation(191, 200, "INTERFIXNAAM", "de Visser"),
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
            Annotation(39, 49, "PATIENT", "Jan Jansen"),
            Annotation(54, 71, "PATIENT", "patient J. Jansen"),
            Annotation(76, 93, "URL", "j.jnsen@email.com"),
            Annotation(98, 109, "TELEFOONNUMMER", "06-12345678"),
            Annotation(114, 116, "LEEFTIJD", "64"),
            Annotation(143, 150, "LOCATIE", "Utrecht"),
            Annotation(164, 174, "DATUM", "10 oktober"),
            Annotation(185, 200, "PERSOON", "Peter de Visser"),
            Annotation(234, 238, "INSTELLING", "umcu"),
        ]
        self.assertEqual(expected_annotations, annotations)

    def test_get_annotations_leading_space(self):
        annotated_text = "Overleg gehad met <PERSOON Jan Jansen>"
        tags = ["<PERSOON Jan Jansen>"]
        annotations = utility.get_annotations(annotated_text, tags, 1)
        self.assertEqual(1, len(annotations))
        self.assertEqual(19, annotations[0].start_ix)

    def test_normalize_value(self):
        ascii_str = "Something about Vincent Menger!"
        value = utility._normalize_value("¡" + ascii_str)
        self.assertEqual(ascii_str, value)

    def test_read_list_unique(self):
        list_name = "input_file_name"
        with patch.object(codecs, "open", return_value=["item", "item"]) as _:
            read_list = utility.read_list(list_name, unique=True)
        self.assertEqual(["item"], read_list)

    def test_read_list_non_unique(self):
        list_name = "input_file_name"
        with patch.object(codecs, "open", return_value=["item", "item"]) as _:
            read_list = utility.read_list(list_name, unique=False)
        self.assertEqual(["item", "item"], read_list)

    def test_flatten_text_all_phi(self):
        spans = [TokenGroup([Token(0, 4, 'UMC ', ''), Token(4, 11, 'Utrecht', 'LOCATIE')], 'INSTELLING')]
        flattened = utility.flatten_text_all_phi(spans)
        self.assertEqual([TokenGroup([Token(0, 4, 'UMC ', ''), Token(4, 11, 'Utrecht', '')], 'INSTELLING')], flattened)

    def test_flatten_text_all_phi_no_nested(self):
        text = "Peter came today and said he loved the UMC"
        spans = tokenize(text)
        spans[0] = Token(0, 5, 'Peter', 'PERSOON')
        spans[-1] = Token(len(text)-3, len(text), 'UMC', 'INSTELLING')
        flattened = utility.flatten_text_all_phi(spans)
        self.assertEqual(spans, flattened)

    def test_flatten_text_all_phi_extra_flat(self):
        spans = [TokenGroup([Token(0, 4, 'UMC ', ''), Token(4, 11, 'Utrecht', 'LOCATIE')], 'INSTELLING'),
                 Token(11, 36, ' is the best hospital in ', ''),
                 Token(36, 43, 'Utrecht', 'LOCATIE')]
        flattened = utility.flatten_text_all_phi(spans)
        expected = [TokenGroup([Token(0, 4, 'UMC ', ''), Token(4, 11, 'Utrecht', '')], 'INSTELLING')] + spans[1:]
        self.assertEqual(
            expected,
            flattened,
        )

    def test_flatten_text_all_phi_extra_nested(self):
        spans = [TokenGroup([Token(0, 4, 'UMC ', ''), Token(4, 11, 'Utrecht', 'LOCATIE')], 'INSTELLING'),
                 Token(11, 27, ' was founded by ', ''),
                 TokenGroup([Token(27, 35, 'Jan van ', ''), Token(35, 44, 'Apeldoorn', 'LOCATIE')], 'PERSOON')]
        flattened = utility.flatten_text_all_phi(spans)
        expected = [TokenGroup([Token(0, 4, 'UMC ', ''), Token(4, 11, 'Utrecht', '')], 'INSTELLING')] + \
                   spans[1:len(spans)-1] + \
                   [TokenGroup([Token(27, 35, 'Jan van ', ''), Token(35, 44, 'Apeldoorn', '')], 'PERSOON')]
        self.assertEqual(
            expected,
            flattened,
        )

    def test_flatten_text_people(self):
        """<INITIAL A <NAME Surname>> are flattened to <INITIALNAME A Surname>"""
        original_tokens = [Token(0, 2, 'A ', ''), Token(2, 9, 'Surname', 'NAME')]
        token_group = TokenGroup(original_tokens, 'INITIAL')
        new_tokens = [Token(0, 2, 'A ', ''), Token(2, 9, 'Surname', '')]
        new_token_group = TokenGroup(new_tokens, 'PERSOON')
        flattened = utility.flatten_text([token_group])
        self.assertEqual([new_token_group], flattened)

    def test_flatten_text_including_non_annotated_tokens(self):
        # <INITIAL A <NAME Surname>> kwam
        original_tokens = [Token(0, 2, 'A ', ''), Token(2, 9, 'Surname', 'NAME')]
        token_group = TokenGroup(original_tokens, 'INITIAL')
        spans = [token_group, Token(9, 10, ' ', ''), Token(10, 14, 'kwam', '')]
        flattened = utility.flatten_text(spans)
        new_tokens = [Token(0, 2, 'A ', ''), Token(2, 9, 'Surname', '')]
        new_token_group = TokenGroup(new_tokens, 'PERSOON')
        new_spans = [new_token_group, Token(9, 10, ' ', ''), Token(10, 14, 'kwam', '')]
        self.assertEqual(new_spans, flattened)

    def test_flatten_text_join_adjacent(self):
        spans = [Token(0, 2, 'de', ''), Token(2, 3, ' ', ''), Token(3, 7, 'naam', ''), Token(7, 8, ' ', ''),
                 Token(8, 11, 'Jan', 'VOORNAAMPAT'), Token(11, 12, ' ', ''), Token(12, 18, 'Jansen', 'ACHTERNAAMPAT')]
        flattened = utility.flatten_text(spans)
        expected_group = TokenGroup(
            [Token(8, 11, 'Jan', ''), Token(11, 12, ' ', ''), Token(12, 18, 'Jansen', '')],
            'PATIENT'
        )
        # noinspection PyTypeChecker
        expected = spans[:4] + [expected_group]
        self.assertEqual(expected, flattened)

    def test_flatten_text_overlapping(self):
        # P. Gomez, G. Perez -> <PERSOON P. Gomez>, <PERSOON G. Perez>
        # [Drs. K[0:6] (PREFIXNAAM), . [6:8], Maijer[8:14] (ACHTERNAAMONBEKEND), ,                                 [14:48], Drs. P[48:54] (PREFIXNAAM), .[54:55], K.H. Deschamps[55:69] (INITIAAL)]
        spans = [TokenGroup([Token(0, 3, 'Drs', ''), Token(3, 5, '. ', ''), Token(5, 6, 'K', '')], 'PREFIXNAAM'),
                 Token(6, 8, '. ', ''),
                 Token(8, 14, 'Suarez', 'ACHTERNAAMONBEKEND'),
                 Token(14, 16, ', ', ''),
                 TokenGroup([Token(0, 3, 'Drs', ''), Token(3, 5, '. ', ''), Token(5, 6, 'K', '')], 'PREFIXNAAM'),
                 Token(6, 8, '. ', ''),
                 Token(8, 14, 'Romero', 'ACHTERNAAMONBEKEND')]
        flattened = utility.flatten_text(spans)
        expected = [TokenGroup([TokenGroup([Token(0, 3, 'Drs', ''), Token(3, 5, '. ', ''), Token(5, 6, 'K', '')], ''),
                                Token(6, 8, '. ', ''),
                                Token(8, 14, 'Suarez', '')], 'PERSOON'),
                    Token(14, 16, ', ', ''),
                    TokenGroup([TokenGroup([Token(0, 3, 'Drs', ''), Token(3, 5, '. ', ''), Token(5, 6, 'K', '')], ''),
                                Token(6, 8, '. ', ''),
                                Token(8, 14, 'Romero', '')], 'PERSOON')]
        self.assertEqual(expected, flattened)


if __name__ == "__main__":
    unittest.main()
