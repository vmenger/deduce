from ddt.datastructures import DatastructCollection, LookupTrie

from deduce.lookup.lookup_lists import get_lookup_lists
from deduce.tokenizer import tokenize_split

lookup_lists = get_lookup_lists()


def _get_institution_trie():

    institution_trie = LookupTrie()

    for institution in lookup_lists["institutions"]:
        institution_trie.add(tokenize_split(institution))

    return institution_trie


def _get_residences_trie():

    residences_trie = LookupTrie()

    for residence in lookup_lists["residences"]:
        residences_trie.add(tokenize_split(residence))

    return residences_trie


def get_lookup_tries():

    lookup_tries = DatastructCollection()

    lookup_trie_mapping = {
        "institutions": _get_institution_trie,
        "residences": _get_residences_trie,
    }

    for name, init_function in lookup_trie_mapping.items():
        lookup_tries[name] = init_function()

    return lookup_tries
