import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import docdeid as dd
from docdeid.tokenizer import Tokenizer

from deduce.data.lookup_lists.src import all_lists
from deduce.str.processor import (
    FilterBasedOnLookupSet,
    TitleCase,
    UpperCase,
    UpperCaseFirstChar,
)
from deduce.utils import optional_load_items, optional_load_json, str_variations

_SRC_SUBDIR = "src"
_CACHE_SUBDIR = "cache"


def lookup_set_to_trie(
    lookup_set: dd.ds.LookupSet, tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """
    Converts a LookupSet into an equivalent LookupTrie.

    Args:
        lookup_set: The input LookupSet
        tokenizer: The tokenizer used to create sequences

    Returns: A LookupTrie with the same items and matching pipeline as the
    input LookupSet.
    """

    trie = dd.ds.LookupTrie(matching_pipeline=lookup_set.matching_pipeline)

    for item in lookup_set.items():
        trie.add_item([token.text for token in tokenizer.tokenize(item)])

    return trie


def apply_transform(items: set[str], transform_config: dict) -> set[str]:
    """
    Applies a transformation to a set of items.

    Args:
        items: The input items.
        transform_config: The trasnformation, including configuration (see
        transform.json for examples).

    Returns: The transformed items.
    """

    strip_lines = transform_config.get("strip_lines", True)
    transforms = transform_config.get("transforms", {})

    for _, transform in transforms.items():

        to_add = []

        for item in items:
            to_add += str_variations(item, transform)

        items.update(to_add)

    if strip_lines:
        items = {i.strip() for i in items}

    return items


def load_raw_items(path: Path) -> set[str]:
    """
    Load the raw items from a lookup list. This works by loading the data in items.txt,
    removing the data in exceptions.txt (if any), and then applying the transformations
    in transform_config.json (if any). If there are nested lookup lists, they will be
    loaded and all treated as items.

    Args:
        path: The path.

    Returns: The raw items, as a set of strings.
    """

    items = optional_load_items(path / "items.txt")
    exceptions = optional_load_items(path / "exceptions.txt")

    sub_list_dirs = list(path.glob("lst_*"))

    if items is None and len(sub_list_dirs) == 0:
        raise RuntimeError(
            f"Cannot import lookup list {path}, did not find "
            f"items.txt or any sublists."
        )

    if exceptions is not None:
        items -= exceptions

    for sub_list_dir in sub_list_dirs:
        items = items.union(load_raw_items(sub_list_dir))

    transform_config = optional_load_json(path / "transform.json")

    if transform_config is not None:
        items = apply_transform(items, transform_config)

    return items


def load_raw_itemsets(base_path: Path, list_names: list[str]) -> dict[str, set[str]]:
    """
    Loads one or more raw itemsets. Automatically parses its name from the folder name.

    Args:
        base_path: The base path to open the raw items.
        list_names: THe lists to load.

    Returns: The raw itemsetes, represented as a dictionary mapping the name of the
    lookup list to a set of strings.
    """

    lists = {}

    for lst in list_names:

        name = lst.split("/")[-1]
        name = name.removeprefix("lst_")

        lists[name] = load_raw_items(base_path / _SRC_SUBDIR / lst)

    return lists


def _load_prefix_lookup(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Load prefix LookupSet (e.g. 'dr', 'mw')"""

    prefix = dd.ds.LookupSet()

    prefix.add_items_from_iterable(raw_itemsets["prefix"])
    prefix.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])

    return prefix


def _load_first_name_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load first_name LookupSet."""

    first_name = dd.ds.LookupSet()

    first_name.add_items_from_iterable(
        raw_itemsets["first_name"],
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    first_name.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(
                filter_set=_load_whitelist(raw_itemsets), case_sensitive=False
            ),
        ],
        replace=True,
    )

    return lookup_set_to_trie(first_name, tokenizer)


def _load_interfix_lookup(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Load interfix LookupSet ('van der', etc.)"""

    interfix = dd.ds.LookupSet()

    interfix.add_items_from_iterable(raw_itemsets["interfix"])
    interfix.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])
    interfix.add_items_from_self(cleaning_pipeline=[TitleCase()])
    interfix.remove_items_from_iterable(["V."])

    return interfix


def _load_surname_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load surname LookupSet."""

    surname = dd.ds.LookupSet()

    surname.add_items_from_iterable(
        raw_itemsets["surname"],
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    surname.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(
                filter_set=_load_whitelist(raw_itemsets), case_sensitive=False
            ),
        ],
        replace=True,
    )

    return lookup_set_to_trie(surname, tokenizer)


def _load_street_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load street lookupset."""

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


def _load_placename_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load placename LookupSet."""

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
                filter_set=_load_whitelist(raw_itemsets), case_sensitive=False
            ),
        ],
        replace=True,
    )

    return lookup_set_to_trie(placename, tokenizer)


def _load_hospital_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load hopsital LookupSet."""

    hospital = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])

    hospital.add_items_from_iterable(raw_itemsets["hospital"])

    hospital.add_items_from_iterable(raw_itemsets["hospital_abbr"])

    hospital.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )

    return lookup_set_to_trie(hospital, tokenizer)


def _load_institution_lookup(
    raw_itemsets: dict[str, set[str]], tokenizer: Tokenizer
) -> dd.ds.LookupTrie:
    """Load institution LookupSet."""

    institution = dd.ds.LookupSet()
    institution.add_items_from_iterable(
        raw_itemsets["healthcare_institution"],
        cleaning_pipeline=[dd.str.StripString(), dd.str.FilterByLength(min_len=4)],
    )

    institution.add_items_from_self(cleaning_pipeline=[UpperCase()])

    institution.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )
    institution = institution - _load_whitelist(raw_itemsets)

    return lookup_set_to_trie(institution, tokenizer)


def _load_common_word_lookup(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
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


def _load_whitelist(raw_itemsets: dict[str, set[str]]) -> dd.ds.LookupSet:
    """
    Load whitelist LookupSet.

    Composed of medical terms, top 1000 frequent words (except surnames), and stopwords.
    Returns:
    """
    medical_term = dd.ds.LookupSet()

    medical_term.add_items_from_iterable(
        raw_itemsets["medical_term"],
    )

    common_word = _load_common_word_lookup(raw_itemsets)

    stop_word = dd.ds.LookupSet()
    stop_word.add_items_from_iterable(raw_itemsets["stop_word"])

    whitelist = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])
    whitelist.add_items_from_iterable(
        medical_term + common_word + stop_word,
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return whitelist


def _default_lookup_loader(name: str, lists: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Default loader for lookup set, if no specific loader is needed."""

    lookup_set = dd.ds.LookupSet()
    lookup_set.add_items_from_iterable(lists[name])
    return lookup_set


def save_lookup_structs(
    path: Path, lookup_structs: dd.ds.DsCollection, deduce_version: str
) -> None:

    data = {
        "deduce_version": deduce_version,
        "saved_datetime": str(datetime.now()),
        "lookup_structs": lookup_structs,
    }

    with open(path / "cache" / "lookup_data.pickle", "wb") as file:
        pickle.dump(data, file)


def validate_cache(path: Path, data: dict, deduce_version: str) -> bool:

    if data["deduce_version"] != deduce_version:
        return False

    src_path = path / _SRC_SUBDIR

    for file in src_path.glob("**"):
        if datetime.fromtimestamp(os.stat(file).st_mtime) > datetime.fromisoformat(
            data["saved_datetime"]
        ):
            return False

    return True


def load_lookup_structs(
    path: Path, deduce_version: str
) -> Optional[dd.ds.DsCollection]:

    cache_file = path / _CACHE_SUBDIR / "lookup_data.pickle"

    try:
        with open(cache_file, "rb") as file:
            data = pickle.load(file)
    except FileNotFoundError:
        return None

    if validate_cache(path, data, deduce_version):
        return data["lookup_structs"]

    return None


def get_lookup_structs(
    path: Path,
    tokenizer: Tokenizer,
    deduce_version: str,
    build: bool = False,
    save_cache: bool = True,
) -> dd.ds.DsCollection:
    """
    Get all lookupsets.

    Returns:
        A DsCollection with all lookup sets.
    """

    if not build:

        lookup_structs = load_lookup_structs(path, deduce_version)

        if lookup_structs is not None:
            return lookup_structs

    print("Building lookup structures. This may take 1-2 minutes.")

    lookup_structs = dd.ds.DsCollection()
    base_items = load_raw_itemsets(base_path=path, list_names=all_lists)

    lookup_set_loaders = {
        "prefix": _load_prefix_lookup,
        "interfix": _load_interfix_lookup,
        "whitelist": _load_whitelist,
    }

    lookup_trie_loaders = {
        "first_name": _load_first_name_lookup,
        "surname": _load_surname_lookup,
        "street": _load_street_lookup,
        "placename": _load_placename_lookup,
        "hospital": _load_hospital_lookup,
        "healthcare_institution": _load_institution_lookup,
    }

    defaults = (
        set(base_items.keys())
        - set(lookup_set_loaders.keys())
        - set(lookup_trie_loaders.keys())
    )

    for name in defaults:
        lookup_structs[name] = _default_lookup_loader(name, base_items)

    for name, init_function in lookup_set_loaders.items():
        lookup_structs[name] = init_function(base_items)

    for name, init_function in lookup_trie_loaders.items():
        lookup_structs[name] = init_function(base_items, tokenizer)

    if save_cache:
        save_lookup_structs(
            path=path, lookup_structs=lookup_structs, deduce_version=deduce_version
        )

    return lookup_structs
