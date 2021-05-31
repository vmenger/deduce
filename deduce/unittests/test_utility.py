import unittest
from unittest.mock import Mock

from deduce import utility

from deduce.listtrie import ListTrie

from deduce.utility import merge_triebased, merge_tokens, context, flatten_text, flatten
from deduce.utilcls import Token, InvalidTokenError, Annotation


def mock_find_all_prefixes(tokens: list[str]) -> list[list[str]]:
    if len(tokens) > 0 and tokens[0] == "van":
        return [["van"], ["van", " ", "der"]]
    elif len(tokens) > 0 and tokens[0] == "A":
        return [["A", "1"]]
    else:
        return []

class TestUtilityMethods(unittest.TestCase):
    def test_merge_triebased(self):
        input_tokens = [Token("Patient", 0, 7), Token("is", 8, 10), Token("opgenomen", 11, 20), Token("op", 21, 23),
                        Token("A", 24, 25), Token("1", 25, 26)]
        expected_output_tokens = input_tokens[:4] + [Token("A1", 24, 26)]
        mock_trie = ListTrie()
        mock_trie.find_all_prefixes = Mock()
        mock_trie.find_all_prefixes.side_effect = mock_find_all_prefixes
        output_tokens = merge_triebased(input_tokens, mock_trie)
        self.assertEqual(expected_output_tokens, output_tokens)

    def test_merge_triebased_with_space(self):
        input_tokens = [Token("van", 0, 3), Token(" ", 3, 4), Token("der", 4, 7), Token(" ", 7, 8),
                        Token("hoeven", 8, 14)]
        expected_output_tokens = [Token("van der", 0, 7), Token(" ", 7, 8), Token("hoeven", 8, 14)]
        mock_trie = ListTrie()
        mock_trie.find_all_prefixes = Mock()
        mock_trie.find_all_prefixes.side_effect = mock_find_all_prefixes
        output_tokens = merge_triebased(input_tokens, mock_trie)
        self.assertEqual(expected_output_tokens, output_tokens)

    def test_merge_tokens(self):
        tokens = [Token("A", 0, 1), Token("B", 1, 2)]
        expected_merged_token = Token("".join(["A", "B"]), 0, 2)
        self.assertEqual(expected_merged_token, merge_tokens(tokens))

    def test_merge_tokens_overlap(self):
        tokens = [Token("Ala", 0, 3), Token("B", 2, 3)]
        with self.assertRaises(InvalidTokenError) as context:
            merge_tokens(tokens)
        self.assertEqual("overlap", context.exception.code)

    def test_merge_tokens_gap(self):
        tokens = [Token("A", 0, 1), Token("B", 2, 3)]
        with self.assertRaises(InvalidTokenError) as context:
            merge_tokens(tokens)
        self.assertEqual("gap", context.exception.code)

    def test_merge_tokens_empty(self):
        with self.assertRaises(InvalidTokenError) as context:
            merge_tokens([])
        self.assertEqual("empty", context.exception.code)

    def test_context_middle(self):
        tokens = [Token("A0", 0, 2), Token("B", 2, 3), Token("C", 3, 4)]
        prev_token, prev_token_ix, next_token, next_token_ix = context(tokens, 1)
        self.assertEqual(tokens[0], prev_token)
        self.assertEqual(0, prev_token_ix)
        self.assertEqual(tokens[2], next_token)
        self.assertEqual(2, next_token_ix)

    def test_context_first(self):
        tokens = [Token("A0", 0, 2), Token("B", 2, 3), Token("C", 3, 4)]
        prev_token, prev_token_ix, next_token, next_token_ix = context(tokens, 0)
        self.assertIsNone(prev_token)
        self.assertEqual(-1, prev_token_ix)
        self.assertEqual(tokens[1], next_token)
        self.assertEqual(1, next_token_ix)

    def test_context_last(self):
        tokens = [Token("A0", 0, 2), Token("B", 2, 3), Token("C", 3, 4)]
        prev_token, prev_token_ix, next_token, next_token_ix = context(tokens, 2)
        self.assertEqual(tokens[1], prev_token)
        self.assertEqual(1, prev_token_ix)
        self.assertIsNone(next_token)
        self.assertEqual(len(tokens), next_token_ix)

    def test_flatten_text(self):
        raw_text = "A Surname"
        annotations = [Annotation(2, 9, "NAME", "Surname"), Annotation(0, 9, "INITIAL", "A Surname")]
        flattened_annotations = flatten_text(raw_text, annotations)
        self.assertEqual([Annotation(0, 9, "PERSOON", "A Surname")], flattened_annotations)

    def test_merge_consecutive(self):
        raw_text = "Peter.Visser"
        annotations = [Annotation(0, 5, "PERSOON", "Peter"), Annotation(6, 12, "PATIENT", "Visser")]
        flattened = utility.merge_consecutive_names(raw_text, annotations)
        self.assertEqual([Annotation(0, 12, "PERSOONPATIENT", "Peter.Visser")], flattened)

    def test_flatten_consecutive(self):
        raw_text = "Peter.Visser"
        annotations = [Annotation(0, 5, "PERSOON", "Peter"), Annotation(6, 12, "PATIENT", "Visser")]
        flattened = utility.flatten_text(raw_text, annotations)
        self.assertEqual([Annotation(0, 12, "PATIENT", "Peter.Visser")], flattened)

    def test_no_flatten_consecutive(self):
        raw_text = "Peter/Visser"
        annotations = [Annotation(0, 5, "PERSOON", "Peter"), Annotation(6, 12, "PATIENT", "Visser")]
        flattened = utility.merge_consecutive_names(raw_text, annotations)
        self.assertEqual(annotations, flattened)

    def test_flatten(self):
        annotations = [Annotation(0, 12, "PERSOON", "Peter Visser"),
                       Annotation(0, 5, "VOORNAAM", "Peter"),
                       Annotation(6, 12, "ACHTERNAAM", "Visser")]
        flattened = flatten(annotations)
        self.assertEqual(Annotation(0, 12, "PERSOONVOORNAAMACHTERNAAM", "Peter Visser"), flattened)

    def test_group_tags(self):
        annotations = [Annotation(13, 20, "PATIENT", "Vincent"),
                       Annotation(0, 12, "PERSOON", "Peter Visser"),
                       Annotation(0, 5, "VOORNAAM", "Peter"),
                       Annotation(6, 12, "ACHTERNAAM", "Visser")]
        groups = utility.group_tags(annotations)
        self.assertEqual(2, len(groups))
        self.assertEqual([Annotation(0, 12, "PERSOON", "Peter Visser"),
                       Annotation(0, 5, "VOORNAAM", "Peter"),
                       Annotation(6, 12, "ACHTERNAAM", "Visser")], groups[0])
        self.assertEqual([Annotation(13, 20, "PATIENT", "Vincent")], groups[1])

    def test_is_whitespace(self):
        self.assertFalse(utility.is_blank_period_hyphen_comma("/"))
        self.assertTrue(utility.is_blank_period_hyphen_comma("."))
        self.assertTrue(utility.is_blank_period_hyphen_comma(".,"))
        self.assertTrue(utility.is_blank_period_hyphen_comma(". "))
        self.assertTrue(utility.is_blank_period_hyphen_comma(".."))

if __name__ == "__main__":
    unittest.main()
