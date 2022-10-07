""" This module contains all tokenizing functionality """
import regex
from typing import Iterable, Optional

import docdeid.tokenize.tokenizer
from docdeid.ds.lookup import LookupTrie

from deduce import utility


class Tokenizer(docdeid.BaseTokenizer):

    def __init__(self, merge_terms: Iterable = None):

        super().__init__()

        self._pattern = regex.compile(r"[\p{L}]+|[^\p{L}]+", flags=regex.I | regex.M)
        self._trie = None

        if merge_terms is not None:
            self._trie = LookupTrie()

            for term in merge_terms:
                tokens = [token.text for token in self.split_text(text=term, merge=False)]
                self._trie.add(tokens)

    def _merge_triebased(self, tokens: list[docdeid.Token]) -> list[docdeid.Token]:

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
                tokens_merged.append(self.join_tokens(tokens[i : i + num_tokens_to_merge]))
                i += num_tokens_to_merge

        return tokens_merged

    @staticmethod
    def join_tokens(tokens: list[docdeid.Token]):

        return docdeid.Token(
            text="".join(token.text for token in tokens),
            start_char=tokens[0].start_char,
            end_char=tokens[-1].end_char,
        )

    @staticmethod
    def _matches_to_tokens(matches: list[regex.Match]) -> list[docdeid.Token]:

        return [
            docdeid.Token(text=match.group(0), start_char=match.span()[0], end_char=match.span()[1])
            for match in matches
        ]

    def split_text(self, text: str, merge: bool = True) -> list[docdeid.Token]:

        if merge and self._trie is None:
            raise AttributeError("Trying to use the tokenize with merging, but no merge terms specified.")

        tokens = self._matches_to_tokens(self._pattern.finditer(text))

        if merge:
            tokens = self._merge_triebased(tokens)

        return tokens

    @staticmethod
    def previous_token(position: int, tokens: list[docdeid.Token]) -> Optional[docdeid.Token]:

        if position == 0:
            return None

        for token in tokens[position - 1 :: -1]:

            if token.text[0].isalpha():
                return token

            if token.text[0] == "(" or token.text[0] == "<" or utility.any_in_text(["\n", "\r", "\t"], token.text):
                return None

        return None

    @staticmethod
    def next_token(position: int, tokens: list[docdeid.Token]) -> Optional[docdeid.Token]:

        if position == len(tokens):
            return None

        for token in tokens[position + 1 :]:

            if token.text[0].isalpha():
                return token

            if token.text[0] == ")" or token.text[0] == ">" or utility.any_in_text(["\n", "\r", "\t"], token.text):
                return None


        return None
