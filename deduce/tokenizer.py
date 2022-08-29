""" This module contains all tokenizing functionality """
from enum import Enum, auto
from typing import Iterable

import docdeid
import docdeid.tokenizer.tokenizer


class _CharType(Enum):

    ALPHA = auto()
    HOOK = auto()
    OTHER = auto()


class Tokenizer(docdeid.BaseTokenizer):
    def __init__(self, merge_terms: Iterable = None):

        self._trie = None

        if merge_terms is not None:
            self._trie = docdeid.datastructures.LookupTrie()

            for term in merge_terms:
                tokens = [token.text for token in self.tokenize(text=term, merge=False)]
                self._trie.add(tokens)

    @staticmethod
    def _character_type(char: str) -> _CharType:

        if char.isalpha():
            return _CharType.ALPHA

        if char in ("<", ">"):
            return _CharType.HOOK

        return _CharType.OTHER

    def _merge_triebased(self, tokens: list[docdeid.Token]) -> list[docdeid.Token]:
        """
        This function merges all sublists of tokens that occur in the trie to one element
        in the list of tokens. For example: if the tree contains ["A", "1"],
        then in the list of tokens ["Patient", "is", "opgenomen", "op", "A", "1"]  the sublist
        ["A", "1"] can be found in the Trie and will thus be merged,
        resulting in ["Patient", "is", "opgenomen", "op", "A1"]
        """

        tokens_text = [token.text for token in tokens]
        tokens_merged = []
        i = 0

        # Iterate over tokens
        while i < len(tokens):

            # Check for each item until the end if there are prefixes of the list in the Trie
            longest_matching_prefix = self._trie.longest_matching_prefix(
                tokens_text[i:]
            )

            # If no prefixes are in the Trie, append the first token and move to the next one
            if longest_matching_prefix is None:
                tokens_merged.append(tokens[i])
                i += 1

            # Else check the maximum length list of tokens, append it to the list that will be returned,
            # and then skip all the tokens in the list
            else:
                num_tokens_to_merge = len(longest_matching_prefix)
                tokens_merged.append(
                    self.join_tokens(tokens[i : i + num_tokens_to_merge])
                )
                i += num_tokens_to_merge

        return tokens_merged

    @staticmethod
    def join_tokens(tokens: list[docdeid.Token]):

        return docdeid.Token(
            text="".join(token.text for token in tokens),
            start_char=tokens[0].start_char,
            end_char=tokens[-1].end_char,
        )

    def tokenize(self, text: str, merge: bool = True) -> list[docdeid.Token]:

        if merge and self._trie is None:
            raise AttributeError(
                "Trying to use the tokenize with merging, but no merge terms specified."
            )

        tokens = []
        last_split = 0
        nested_hook_counter = 0

        # Iterate over all chars in the text
        for index, char in enumerate(text):

            if index == 0:
                continue

            # Keeps track of how deep in tags we are
            if text[index - 1] == "<":
                nested_hook_counter += 1
                continue

            if text[index] == ">":
                nested_hook_counter -= 1
                continue

            # Never split if we are in a tag
            if nested_hook_counter > 0:
                continue

            # Split if we transition between alpha, hook and other
            if self._character_type(char) != self._character_type(text[index - 1]):
                tokens.append(
                    docdeid.Token(
                        start_char=last_split,
                        end_char=index,
                        text=text[last_split:index],
                    )
                )
                last_split = index

        # Append the tokens
        tokens.append(
            docdeid.Token(
                start_char=last_split, end_char=len(text), text=text[last_split:]
            )
        )

        if merge:
            tokens = self._merge_triebased(tokens)

        return tokens

    @staticmethod
    def join_tokens_as_text(tokens: list[str]) -> str:

        return "".join(tokens)

    def tokenize_as_text(self, text: str, merge: bool = True) -> list[str]:

        return [token.text for token in self.tokenize(text=text, merge=merge)]
