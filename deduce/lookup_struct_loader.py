"""Some functions for creating lookup structures from raw items."""

import docdeid as dd
from docdeid import Tokenizer

from deduce.str import FilterBasedOnLookupSet, TitleCase, UpperCase, UpperCaseFirstChar
from deduce.utils import lookup_set_to_trie


def load_common_word_lookup(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Load common_word LookupSet."""

    common_word = dd.ds.LookupSet()
    common_word.add_items_from_iterable(
        raw_itemsets["common_word"],
    )

    surnames_lowercase = dd.ds.LookupSet()
    surnames_lowercase.add_items_from_iterable(
        raw_itemsets["surname"],
        cleaning_pipeline=[
            dd.str.LowercaseString(),
            dd.str.FilterByLength(min_len=2),
        ],
    )

    common_word -= surnames_lowercase

    return common_word


def load_whitelist_lookup(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
    """
    Load whitelist LookupSet.

    Composed of medical terms, top 1000 frequent words (except surnames), and stopwords.
    """
    medical_term = dd.ds.LookupSet()

    medical_term.add_items_from_iterable(
        raw_itemsets["medical_term"],
    )

    common_word = load_common_word_lookup(raw_itemsets)

    stop_word = dd.ds.LookupSet()
    stop_word.add_items_from_iterable(raw_itemsets["stop_word"])

    whitelist = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])
    whitelist.add_items_from_iterable(
        medical_term + common_word + stop_word,
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return whitelist


def load_eponymous_disease_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Loads eponymous disease LookupTrie (e.g. Henoch-Schonlein)."""
    epo_disease = dd.ds.LookupSet()
    epo_disease.add_items_from_iterable(raw_itemsets["eponymous_disease"])
    epo_disease.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()]
    )

    return lookup_set_to_trie(epo_disease, tokenizer)


def load_prefix_lookup(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Load prefix LookupSet (e.g. 'dr', 'mw')."""

    prefix = dd.ds.LookupSet()

    prefix.add_items_from_iterable(raw_itemsets["prefix"])
    prefix.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])

    return prefix


def load_first_name_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load first_name LookupTrie."""

    first_name = dd.ds.LookupSet()

    first_name.add_items_from_iterable(
        raw_itemsets["first_name"],
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    first_name.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(
                filter_set=load_whitelist_lookup(raw_itemsets), case_sensitive=False
            ),
        ],
        replace=True,
    )

    return lookup_set_to_trie(first_name, tokenizer)


def load_interfix_lookup(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Load interfix LookupSet ('van der', etc.)."""

    interfix = dd.ds.LookupSet()

    interfix.add_items_from_iterable(raw_itemsets["interfix"])
    interfix.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])
    interfix.add_items_from_self(cleaning_pipeline=[TitleCase()])
    interfix.remove_items_from_iterable(["V."])

    return interfix


def load_surname_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load surname LookupTrie."""

    surname = dd.ds.LookupSet()

    surname.add_items_from_iterable(
        raw_itemsets["surname"],
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    surname.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(
                filter_set=load_whitelist_lookup(raw_itemsets), case_sensitive=False
            ),
        ],
        replace=True,
    )

    return lookup_set_to_trie(surname, tokenizer)


def load_street_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load street LookupTrie."""

    street = dd.ds.LookupSet()

    street.add_items_from_iterable(
        raw_itemsets["street"],
        cleaning_pipeline=[
            dd.str.StripString(),
            dd.str.FilterByLength(min_len=4),
        ],
    )

    street.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()])

    return lookup_set_to_trie(street, tokenizer)


def load_placename_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load placename LookupTrie."""

    placename = dd.ds.LookupSet()

    placename.add_items_from_iterable(
        raw_itemsets["placename"],
        cleaning_pipeline=[
            dd.str.StripString(),
        ],
    )

    placename.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()]
    )

    placename.add_items_from_self(
        cleaning_pipeline=[
            dd.str.ReplaceValue("(", ""),
            dd.str.ReplaceValue(")", ""),
            dd.str.ReplaceValue("  ", " "),
        ]
    )

    placename.add_items_from_self(cleaning_pipeline=[UpperCase()])

    placename.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(
                filter_set=load_whitelist_lookup(raw_itemsets), case_sensitive=False
            ),
        ],
        replace=True,
    )

    return lookup_set_to_trie(placename, tokenizer)


def load_hospital_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load hopsital LookupTrie."""

    hospital = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])

    hospital.add_items_from_iterable(raw_itemsets["hospital"])

    hospital.add_items_from_iterable(raw_itemsets["hospital_abbr"])

    hospital.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )

    return lookup_set_to_trie(hospital, tokenizer)


def load_institution_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load institution LookupTrie."""

    institution = dd.ds.LookupSet()
    institution.add_items_from_iterable(
        raw_itemsets["healthcare_institution"],
        cleaning_pipeline=[dd.str.StripString(), dd.str.FilterByLength(min_len=4)],
    )

    institution.add_items_from_self(cleaning_pipeline=[UpperCase()])

    institution.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )
    institution = institution - load_whitelist_lookup(raw_itemsets)

    return lookup_set_to_trie(institution, tokenizer)
