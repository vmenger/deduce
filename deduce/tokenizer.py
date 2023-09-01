import re
from typing import Iterable, Optional

import docdeid as dd
import regex

TOKENIZER_PATTERN = regex.compile(r"\w+|[\n\r\t]|.(?<! )", flags=re.I | re.M)


class DeduceToken(dd.tokenize.Token):
    """Deduce token, which implements next alpha logic."""

    def next_alpha(self, num: int = 1) -> Optional[dd.tokenize.Token]:
        """Find the next alpha token, if any."""

        cntr = 0
        next_token = self.next()

        while True:

            if next_token is None:
                return None

            if next_token.text in {")", ">", "\n", "\r", "\t"}:
                return None

            if next_token.text[0].isalpha():

                cntr += 1

                if cntr == num:
                    return next_token

            next_token = next_token.next()

    def previous_alpha(self, num: int = 1) -> Optional[dd.tokenize.Token]:
        """Find the previous alpha token, if any."""

        cntr = 0
        previous_token = self.previous()

        while True:

            if previous_token is None:
                return None

            if previous_token.text in {"(", "<", "\n", "\r", "\t"}:
                return None

            if previous_token.text[0].isalpha():

                cntr += 1

                if cntr == num:
                    return previous_token

            previous_token = previous_token.previous()


class DeduceTokenizer(dd.tokenize.Tokenizer):
    """
    Tokenizes text, where a token is any sequence of alphanumeric characters (case insensitive), a single newline/tab
    character, or a single special character. It does not include whitespaces as tokens.

    Arguments:
        merge_terms: An iterable of strings that should not be split (i.e. always returned as tokens).
    """

    def __init__(self, merge_terms: Optional[Iterable] = None) -> None:
        super().__init__()

        self._pattern = TOKENIZER_PATTERN
        self._trie = None

        if merge_terms is not None:

            trie = dd.ds.LookupTrie()

            for term in merge_terms:
                tokens = [token.text for token in self._split_text(text=term)]
                trie.add_item(tokens)

            self._trie = trie

    @staticmethod
    def _join_tokens(text: str, tokens: list[dd.tokenize.Token]) -> dd.tokenize.Token:
        """
        Join a list of tokens into a single token. Does this by joining together the text, and taking the first Token'
        ``start_char`` and last Token' ``end_char``. Note that this only makes sense for the current non- destructive
        tokenizing logic.

        Args:
            tokens: The input tokens.

        Returns:
            The output token.
        """

        return DeduceToken(
            text=text[tokens[0].start_char : tokens[-1].end_char],
            start_char=tokens[0].start_char,
            end_char=tokens[-1].end_char,
        )

    def _merge(self, text: str, tokens: list[dd.tokenize.Token]) -> list[dd.tokenize.Token]:
        """
        Merge a list of tokens based on the trie.

        Args:
            tokens: A list of tokens, with merge_terms split.

        Returns:
            A list of tokens, with merge_terms joined in single tokens.
        """

        tokens_text = [token.text for token in tokens]
        tokens_merged = []
        i = 0

        while i < len(tokens):

            longest_matching_prefix = self._trie.longest_matching_prefix(tokens_text[i:])

            if longest_matching_prefix is None:
                tokens_merged.append(tokens[i])
                i += 1

            else:
                num_tokens_to_merge = len(longest_matching_prefix)
                tokens_merged.append(self._join_tokens(text, tokens[i : i + num_tokens_to_merge]))
                i += num_tokens_to_merge

        return tokens_merged

    def _split_text(self, text: str) -> list[dd.tokenize.Token]:
        """
        Split text, based on the regexp pattern.

        Args:
            text: The input text.

        Returns:
            A list of tokens.
        """

        tokens = []

        for match in self._pattern.finditer(text):
            tokens.append(DeduceToken(text=match.group(0), start_char=match.span()[0], end_char=match.span()[1]))

        if self._trie is not None:
            tokens = self._merge(text, tokens)

        return tokens
