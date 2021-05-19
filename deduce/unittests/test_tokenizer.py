import unittest
from unittest.mock import patch

from deduce import tokenizer
from deduce.tokenizer import tokenize_split, NOSPLIT_TRIE
from deduce.utilcls import Token


class TestTokenizerMethods(unittest.TestCase):
    def test_tokenize_split(self):
        tokens = tokenize_split("Peter Parker", False)
        self.assertEqual(3, len(tokens))
        self.assertEqual([Token("Peter", 0, 5), Token(" ", 5, 6), Token("Parker", 6, 12)], tokens)

    def test_tokenize_split_merge(self):
        with patch.object(tokenizer, "merge_triebased") as mock:
            tokenize_split("text", True)
        mock.assert_called_with(tokenize_split("text", False), NOSPLIT_TRIE)

if __name__ == "__main__":
    unittest.main()
