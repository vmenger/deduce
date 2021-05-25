import unittest
from unittest.mock import Mock

from deduce.listtrie import ListTrie

from deduce.utility import merge_triebased, merge_tokens, context
from deduce.utilcls import Token, InvalidTokenError


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


if __name__ == "__main__":
    unittest.main()
