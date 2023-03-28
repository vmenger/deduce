import re
from typing import Iterable, Optional

import docdeid as dd
import regex

from deduce import utils


class DeduceTokenizer(dd.Tokenizer):
    """
    This tokenizes text according to the specific Deduce logic. It uses the regexp pattern ``[\p{L}]+|[^\p{L}]+`` (case
    insensitive), which is equivalent to splitting when going from alpha characters to non-alpha characters. It includes
    whitespaces as tokens.

    Arguments:
        merge_terms: An iterable of strings that should not be split (i.e. always returned as tokens).
    """

    def __init__(self, merge_terms: Optional[Iterable] = None) -> None:
        super().__init__()

        self._pattern = regex.compile(r"[\p{L}]+|[^\p{L}]+", flags=re.I | re.M)
        self._trie = None

        if merge_terms is not None:

            trie = dd.ds.LookupTrie()

            for term in merge_terms:
                tokens = [token.text for token in self._split_text(text=term)]
                trie.add_item(tokens)

            self._trie = trie

    def _merge(self, tokens: list[dd.Token]) -> list[dd.Token]:
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
                tokens_merged.append(self._join_tokens(tokens[i : i + num_tokens_to_merge]))
                i += num_tokens_to_merge

        return tokens_merged

    @staticmethod
    def _join_tokens(tokens: list[dd.Token]) -> dd.Token:
        """
        Join a list of tokens into a single token. Does this by joining together the text, and taking the first Token'
        ``start_char`` and last Token' ``end_char``. Note that this only makes sense for the current non- destructive
        tokenizing logic.

        Args:
            tokens: The input tokens.

        Returns:
            The output token.
        """

        return dd.Token(
            text="".join(token.text for token in tokens),
            start_char=tokens[0].start_char,
            end_char=tokens[-1].end_char,
        )

    @staticmethod
    def _matches_to_tokens(matches: list[regex.Match]) -> list[dd.Token]:
        """
        Create tokens from regexp matches.

        Args:
            matches: The matches.

        Returns:
            The tokens.
        """

        return [
            dd.Token(text=match.group(0), start_char=match.span()[0], end_char=match.span()[1]) for match in matches
        ]

    def _split_text(self, text: str) -> list[dd.Token]:
        """
        Split text, based on the regexp pattern.

        Args:
            text: The input text.

        Returns:
            A list of tokens.
        """

        matches = self._pattern.finditer(text)
        tokens = self._matches_to_tokens(matches)

        if self._trie is not None:
            tokens = self._merge(tokens)

        return tokens

    @staticmethod
    def _previous_token(position: int, tokens: list[dd.Token]) -> Optional[dd.Token]:
        """
        Logic for previous token. Only returns tokens that start with an alpha character, and never returns when a
        ``(``, ``<`` or newline character is found.

        Args:
            position: The position to start looking for the previous token.
            tokens: The full list of tokens.

        Returns:
            The previous token, if any, else ``None``.
        """

        if position == 0:
            return None

        for token in tokens[position - 1 :: -1]:

            if token.text[0].isalpha():
                return token

            if token.text[0] == "(" or token.text[0] == "<" or utils.any_in_text(["\n", "\r", "\t"], token.text):
                return None

        return None

    @staticmethod
    def _next_token(position: int, tokens: list[dd.Token]) -> Optional[dd.Token]:
        """
        Logic for next token. Only returns tokens that start with an alpha character, and never returns when a ``)``,
        ``>`` or newline character is found.

        Args:
            position: The position to start looking for the next token.
            tokens: The full list of tokens.

        Returns:
            The next token, if any, else ``None``.
        """

        if position == len(tokens):
            return None

        for token in tokens[position + 1 :]:

            if token.text[0].isalpha():
                return token

            if token.text[0] == ")" or token.text[0] == ">" or utils.any_in_text(["\n", "\r", "\t"], token.text):
                return None

        return None
