from typing import Iterable, Optional

import docdeid as dd
import regex

_TOKENIZER_PATTERN = regex.compile(r"\w+|[\n\r\t]| {4,}|[^ ]", flags=regex.I | regex.M)


class DeduceTokenizer(dd.tokenizer.Tokenizer):  # pylint: disable=R0903
    """
    Tokenizes text, where a token is any sequence of alphanumeric characters (case
    insensitive), a single newline/tab character, or a single special character. It does
    not include whitespaces as tokens.

    Arguments:
        merge_terms: An iterable of strings that should not be split (i.e. always
        returned as tokens).
    """

    def __init__(self, merge_terms: Optional[Iterable] = None) -> None:
        super().__init__()

        self._pattern = _TOKENIZER_PATTERN
        self._trie: Optional[dd.ds.LookupTrie] = None

        self._start_words: set[str] = set()

        if merge_terms is not None:
            self._init_merge_structures(merge_terms=merge_terms)

    def _init_merge_structures(self, merge_terms: Iterable) -> None:
        """
        Initializes the merge structures.

        Args:
            merge_terms: The provided terms that should be merged into a single token.
        """

        trie = dd.ds.LookupTrie()

        for term in merge_terms:
            tokens = [token.text for token in self._split_text(text=term)]
            trie.add_item(tokens)
            self._start_words.add(tokens[0])

        self._trie = trie

    @staticmethod
    def _join_tokens(text: str, tokens: list[dd.tokenizer.Token]) -> dd.tokenizer.Token:
        """
        Join a list of tokens into a single token. Does this by creating a new token,
        that ranges from the first token start char to the last token end char.

        Args:
            text: The original text.
            tokens: The input tokens.

        Returns:
            The output token.
        """

        return dd.Token(
            text=text[tokens[0].start_char : tokens[-1].end_char],
            start_char=tokens[0].start_char,
            end_char=tokens[-1].end_char,
        )

    def _merge(
        self, text: str, tokens: list[dd.tokenizer.Token]
    ) -> list[dd.tokenizer.Token]:
        """
        Merge a list of tokens based on the trie.

        Args:
            tokens: A list of tokens, with merge_terms split.

        Returns:
            A list of tokens, with merge_terms joined in single tokens.
        """

        if self._trie is None:
            return tokens

        tokens_text = [token.text for token in tokens]
        tokens_merged = []
        i = 0

        while i < len(tokens):

            if tokens_text[i] not in self._start_words:
                tokens_merged.append(tokens[i])
                i += 1
                continue

            longest_matching_prefix = self._trie.longest_matching_prefix(
                tokens_text, start_i=i
            )

            if longest_matching_prefix is None:
                tokens_merged.append(tokens[i])
                i += 1

            else:
                num_tokens_to_merge = len(longest_matching_prefix)
                tokens_merged.append(
                    self._join_tokens(text, tokens[i : i + num_tokens_to_merge])
                )
                i += num_tokens_to_merge

        return tokens_merged

    def _split_text(self, text: str) -> list[dd.tokenizer.Token]:
        """
        Split text, based on the regexp pattern.

        Args:
            text: The input text.

        Returns:
            A list of tokens.
        """

        tokens = []

        for match in self._pattern.finditer(text):
            tokens.append(
                dd.Token(
                    text=match.group(0),
                    start_char=match.span()[0],
                    end_char=match.span()[1],
                )
            )

        if self._trie is not None:
            tokens = self._merge(text, tokens)

        return tokens
