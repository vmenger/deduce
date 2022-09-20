""" This module contains all tokenizing functionality """
import itertools
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Iterable, Optional, Union

import docdeid
import docdeid.tokenize.tokenizer
from deduce import utility
from docdeid.ds.lookup import LookupTrie


class _CharType(Enum):

    ALPHA = auto()
    OTHER = auto()


class Tokenizer(docdeid.BaseTokenizer):
    def __init__(self, merge_terms: Iterable = None):

        self._trie = None

        if merge_terms is not None:
            self._trie = LookupTrie()

            for term in merge_terms:
                tokens = [token.text for token in self.tokenize(text=term, merge=False)]
                self._trie.add(tokens)

    @staticmethod
    def _character_type(char: str) -> _CharType:

        if char.isalpha():
            return _CharType.ALPHA

        return _CharType.OTHER

    def _merge_triebased(self, tokens: list[docdeid.Token]) -> list[docdeid.Token]:

        tokens_text = [token.text for token in tokens]
        tokens_merged = []
        i = 0

        while i < len(tokens):

            longest_matching_prefix = self._trie.longest_matching_prefix(
                tokens_text[i:]
            )

            if longest_matching_prefix is None:
                tokens_merged.append(tokens[i])
                i += 1

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
            index=tokens[0].index,
        )

    def tokenize(self, text: str, merge: bool = True) -> list[docdeid.Token]:

        if merge and self._trie is None:
            raise AttributeError(
                "Trying to use the tokenize with merging, but no merge terms specified."
            )

        tokens = []
        last_split = 0

        # Iterate over all chars in the text
        for index, char in enumerate(text):

            if index == 0:
                continue

            # Split if we transition between character types
            if self._character_type(char) != self._character_type(text[index - 1]):
                tokens.append(
                    docdeid.Token(
                        start_char=last_split,
                        end_char=index,
                        text=text[last_split:index],
                        index=0,
                    )
                )
                last_split = index

        # Append the tokens
        tokens.append(
            docdeid.Token(
                start_char=last_split,
                end_char=len(text),
                text=text[last_split:],
                index=0,
            )
        )

        if merge:
            tokens = self._merge_triebased(tokens)

        return [
            docdeid.Token(
                text=token.text,
                start_char=token.start_char,
                end_char=token.end_char,
                index=i,
            )
            for token, i in zip(tokens, itertools.count())
        ]


class TokenContext:
    def __init__(self, position: int, tokens: list[docdeid.Token]):

        self._tokens = tokens
        self._position = position

    @property
    def token(self):
        return self._tokens[self._position]

    def next(self, num: int = 1):

        current_token = self._tokens[self._position]

        for _ in range(num):
            current_token = self._get_next_token(current_token.index)

            if current_token is None:
                return None

        return current_token

    def previous(self, num: int = 1):

        current_token = self._tokens[self._position]

        for _ in range(num):
            current_token = self.get_previous_token(current_token.index)

            if current_token is None:
                return None

        return current_token

    def num_tokens_from_position(self):

        return len(self._tokens) - self._position

    def get_token(self, pos: int):
        return self._tokens[pos]

    def get_token_at_num_from_position(self, num=0):
        return self._tokens[self._position + num]

    def _get_next_token(self, i: int) -> Union[docdeid.Token, None]:

        if i == len(self._tokens):
            return None

        for token in self._tokens[i + 1 :]:

            if (
                token.text[0] == ")"
                or token.text[0] == ">"
                or utility.any_in_text(["\n", "\r", "\t"], token.text)
            ):
                return None

            if token.text[0].isalpha():
                return token

        return None

    def get_previous_token(self, i: int) -> Union[docdeid.Token, None]:

        if i == 0:
            return None

        for token in self._tokens[i - 1 :: -1]:

            if (
                token.text[0] == "("
                or token.text[0] == "<"
                or utility.any_in_text(["\n", "\r", "\t"], token.text)
            ):
                return None

            if token.text[0].isalpha():
                return token

        return None

    @property
    def next_token(self):
        return self.next(1)

    @property
    def previous_token(self):
        return self.previous(1)


class TokenContextPattern(ABC):
    def __init__(self, tag: str):
        self._tag = tag

    def precondition(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> bool:
        return True

    @abstractmethod
    def match(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> Union[bool, tuple[bool, Any]]:
        pass

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:
        return token_context.token, token_context.token, self._tag

    def apply(
        self, token_context: TokenContext, meta_data: Optional[dict] = None
    ) -> Union[None, tuple]:

        if not self.precondition(token_context, meta_data):
            return None

        match = self.match(token_context, meta_data)
        match_info = None

        if isinstance(match, tuple):
            match, match_info = match  # unpack

        if match:
            return self.annotate(token_context, match_info)
