""" This module contains all tokenizing functionality """
from enum import Enum, auto
from typing import Iterable

from docdeid.datastructures import LookupTrie


class _CharType(Enum):

    ALPHA = auto()
    HOOK = auto()
    OTHER = auto()


def _character_type(char: str) -> _CharType:

    if char.isalpha():
        return _CharType.ALPHA

    if char in ("<", ">"):
        return _CharType.HOOK

    return _CharType.OTHER


class Tokenizer:
    def __init__(self, merge_terms: Iterable = None):

        self._trie = None

        if merge_terms is not None:
            self._trie = LookupTrie()

            for term in merge_terms:
                tokens = self.tokenize(text=term, merge=False)
                self._trie.add(tokens)

    @staticmethod
    def join_tokens(tokens):
        return "".join(tokens)

    def _merge_triebased(self, tokens: list[str]) -> list[str]:
        """
        This function merges all sublists of tokens that occur in the trie to one element
        in the list of tokens. For example: if the tree contains ["A", "1"],
        then in the list of tokens ["Patient", "is", "opgenomen", "op", "A", "1"]  the sublist
        ["A", "1"] can be found in the Trie and will thus be merged,
        resulting in ["Patient", "is", "opgenomen", "op", "A1"]
        """

        tokens_merged = []
        i = 0

        # Iterate over tokens
        while i < len(tokens):

            # Check for each item until the end if there are prefixes of the list in the Trie
            prefix_matches = self._trie.find_all_prefixes(tokens[i:])

            # If no prefixes are in the Trie, append the first token and move to the next one
            if len(prefix_matches) == 0:
                tokens_merged.append(tokens[i])
                i += 1

            # Else check the maximum length list of tokens, append it to the list that will be returned,
            # and then skip all the tokens in the list
            else:
                max_list = max(prefix_matches, key=len)
                tokens_merged.append("".join(max_list))
                i += len(max_list)

        return tokens_merged

    def tokenize(self, text: str, merge: bool = True) -> list[str]:

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
            if _character_type(char) != _character_type(text[index - 1]):
                tokens.append(text[last_split:index])
                last_split = index

        # Append the tokens
        tokens.append(text[last_split:])

        if merge:
            tokens = self._merge_triebased(tokens)

        return tokens
