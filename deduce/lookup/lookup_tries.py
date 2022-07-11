from ddt.datastructures import DatastructCollection, LookupTrie

from deduce.lookup.lookup_lists import get_lookup_lists
from deduce.tokenizer import Tokenizer

lookup_lists = get_lookup_lists()


def _get_institution_trie(tokenizer: Tokenizer) -> LookupTrie:

    institution_trie = LookupTrie()

    for institution in lookup_lists["institutions"]:
        institution_trie.add(tokenizer.tokenize(institution, merge=False))

    return institution_trie


def _get_residences_trie(tokenizer: Tokenizer) -> LookupTrie:

    residences_trie = LookupTrie()

    for residence in lookup_lists["residences"]:
        residences_trie.add(tokenizer.tokenize(residence, merge=False))

    return residences_trie


def get_lookup_tries(tokenizer: Tokenizer) -> DatastructCollection:

    lookup_tries = DatastructCollection()

    lookup_trie_mapping = {
        "institutions": _get_institution_trie,
        "residences": _get_residences_trie,
    }

    for name, init_function in lookup_trie_mapping.items():
        lookup_tries[name] = init_function(tokenizer)

    return lookup_tries
