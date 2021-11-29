""" This module contains all tokenizing functionality """
import codecs

from .listtrie import ListTrie
from .utility import get_data
from .utility import merge_triebased
from .utilcls import Token
from .utility import type_of



def tokenize_split(text, merge=True):
    """
    Tokenize a piece of text, where splits are when going from alpha to other,
    and tokens witin < > tags are never split
    """

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
        if type_of(char) != type_of(text[index - 1]):
            tokens.append(Token(text[last_split:index], last_split, index))
            last_split = index

    # Append the tokens
    tokens.append(Token(text[last_split:], last_split, len(text)))

    # If we need to merge based on the nosplit_trie, so do
    if merge:
        return merge_triebased(tokens, NOSPLIT_TRIE)

    # Return
    return tokens

def join_tokens(tokens: list) -> Token:
    """Join a list of tokens together, simple when using the custom tokenize method"""
    if not tokens:
        raise ValueError('Cannot join an empty list of tokens')
    # Assume that the tokens are sorted by start_ix
    return Token(''.join([token.text for token in tokens]), tokens[0].start_ix, tokens[-1].end_ix)


# This trie contains all strings that should be regarded as a single token
# These are: all interfixes, A1-A4, and some special characters like \n, \r and \t
NOSPLIT_TRIE = ListTrie()

# Read interfixes
INTERFIXES = list(
    set(line.strip() for line in codecs.open(get_data("voorvoegsel.lst")))
)
PREFIXES = list(set(line.strip() for line in codecs.open(get_data("prefix.lst"))))

# Fill trie
for interfix in INTERFIXES:
    NOSPLIT_TRIE.add(tokenize_split(interfix, False))

for prefix in PREFIXES:
    NOSPLIT_TRIE.add(tokenize_split(prefix, False))

for value in ["A1", "A2", "A3", "A4", "\n", "\r", "\t"]:
    NOSPLIT_TRIE.add(tokenize_split(value, False))
