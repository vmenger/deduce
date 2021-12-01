import unittest

from deduce.utilcls import Token, TokenGroup


class TestUtilityMethods(unittest.TestCase):
    def test_token_flatten(self):
        token = Token(0, 7, 'pedrito', 'PERSOON')
        flattened = token.flatten()
        self.assertEqual(token, flattened)

    def test_token_flatten_with_annotation(self):
        token = Token(0, 7, 'pedrito', 'PERSOON')
        flattened = token.flatten(with_annotation='PATIENT')
        self.assertEqual(Token(0, 7, 'pedrito', 'PATIENT'), flattened)

    def test_token_group_flatten(self):
        tokens = [Token(0, 7, 'pedrito', 'PERSOON'), Token(8, 12, 'rico', '')]
        token_group = TokenGroup(tokens, 'PATIENT')
        flattened = token_group.flatten()
        self.assertEqual(TokenGroup([Token(0, 7, 'pedrito', ''), tokens[1]], 'PATIENTPERSOON'), flattened)

    def test_token_group_flatten_with_annotation(self):
        tokens = [Token(0, 7, 'pedrito', 'PERSOON'), Token(8, 12, 'rico', '')]
        token_group = TokenGroup(tokens, 'PATIENT')
        flattened = token_group.flatten(with_annotation='LOCATIE')
        self.assertEqual(TokenGroup([Token(0, 7, 'pedrito', ''), tokens[1]], 'LOCATIE'), flattened)

    def test_token_remove_annotation(self):
        token = Token(0, 7, 'pedrito', 'PERSOON')
        no_ann = token.remove_annotation()
        self.assertEqual(Token(0, 7, 'pedrito', ''), no_ann)

    def test_get_flat_token_list(self):
        """<INSTELLING Ziekenhuis <INITIAAL M <ACHTERNAAMONBEKEND Smid>> <INTERFIXNAAM de Vries>>>"""
        tokens = [Token(11, 12, 'M', ''),
                  Token(13, 17, 'Smid', 'ACHTERNAAMONBEKEND'),
                  Token(19, 27, 'de Vries', 'INTERFIXNAAM')]
        token_group = TokenGroup(tokens, 'INITIAAL')
        hospital = Token(0, 10, 'Ziekenhuis', '')
        big_token_group = TokenGroup([hospital, token_group], 'INSTELLING')
        flat_tokens = big_token_group.get_flat_token_list(remove_annotations=False)
        self.assertEqual([hospital] + tokens, flat_tokens)

    def test_get_flat_token_list_remove_annotations(self):
        """<INSTELLING Ziekenhuis <INITIAAL M <ACHTERNAAMONBEKEND Smid>> <INTERFIXNAAM de Vries>>>"""
        tokens = [Token(11, 12, 'M', ''),
                  Token(13, 17, 'Smid', 'ACHTERNAAMONBEKEND'),
                  Token(19, 27, 'de Vries', 'INTERFIXNAAM')]
        token_group = TokenGroup(tokens, 'INITIAAL')
        hospital = Token(0, 10, 'Ziekenhuis', '')
        big_token_group = TokenGroup([hospital, token_group], 'INSTELLING')
        flat_tokens = big_token_group.get_flat_token_list(remove_annotations=True)
        expected = [hospital, tokens[0]] + [Token(13, 17, 'Smid', ''), Token(19, 27, 'de Vries', '')]
        self.assertEqual(expected, flat_tokens)

    def test_token_with_annotation(self):
        token = Token(0, 3, 'Raf', 'PERSOON')
        new_token = Token(0, 3, 'Raf', 'LEGEND')
        self.assertEqual(new_token, token.with_annotation('LEGEND'))

    def test_token_group_with_annotation(self):
        tokens = [Token(0, 3, 'Raf', 'PERSOON'), Token(3, 9, ' Carra', 'LEGEND')]
        token_group = TokenGroup(tokens, 'LEGEND')
        new_token_group = TokenGroup(tokens, 'SINGER')
        self.assertEqual(new_token_group, token_group.with_annotation('SINGER'))


if __name__ == "__main__":
    unittest.main()
