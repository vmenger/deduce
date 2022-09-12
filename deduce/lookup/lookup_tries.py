import docdeid
from docdeid.datastructures import DatastructCollection
from docdeid.tokenizer.tokenizer import BaseTokenizer

from deduce.lookup.lookup_lists import get_lookup_lists

lookup_lists = get_lookup_lists()


def _get_institution_trie(
    tokenizer: BaseTokenizer,
) -> docdeid.datastructures.LookupTrie:

    institution_trie = docdeid.datastructures.LookupTrie()

    for institution in lookup_lists["institutions"]:
        institution_trie.add(
            [token.text for token in tokenizer.tokenize(institution, merge=False)]
        )

    return institution_trie


def _get_residences_trie(tokenizer: BaseTokenizer) -> docdeid.datastructures.LookupTrie:

    residences_trie = docdeid.datastructures.LookupTrie()

    for residence in lookup_lists["residences"]:
        residences_trie.add(
            [token.text for token in tokenizer.tokenize(residence, merge=False)]
        )

    return residences_trie


def get_lookup_tries(tokenizer: BaseTokenizer) -> DatastructCollection:

    lookup_tries = DatastructCollection()

    lookup_trie_mapping = {
        "institutions": _get_institution_trie,
        "residences": _get_residences_trie,
    }

    for name, init_function in lookup_trie_mapping.items():
        lookup_tries[name] = init_function(tokenizer)

    return lookup_tries
