"""Responsible for loading, building and caching all lookup structures."""

import logging
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

import docdeid as dd
from docdeid.tokenizer import Tokenizer


from deduce.depr import DeprecatedDsCollection
from deduce.lookup_struct_loader import (
    load_eponymous_disease_lookup,
    load_first_name_lookup,
    load_hospital_lookup,
    load_institution_lookup,
    load_interfix_lookup,
    load_placename_lookup,
    load_prefix_lookup,
    load_street_lookup,
    load_surname_lookup,
    load_whitelist_lookup,
)
from deduce.utils import apply_transform, optional_load_items, optional_load_json

_SRC_SUBDIR = "src"
_CACHE_SUBDIR = "cache"
_CACHE_FILE = "lookup_structs.pickle"

_LOOKUP_SET_LOADERS = {
    "prefix": load_prefix_lookup,
    "interfix": load_interfix_lookup,
    "whitelist": load_whitelist_lookup,
}

_LOOKUP_TRIE_LOADERS = {
    "first_name": load_first_name_lookup,
    "surname": load_surname_lookup,
    "street": load_street_lookup,
    "placename": load_placename_lookup,
    "hospital": load_hospital_lookup,
    "healthcare_institution": load_institution_lookup,
    "eponymous_disease": load_eponymous_disease_lookup,
}


def load_raw_itemset(path: Path) -> set[str]:
    """
    Load the raw items from a lookup list. This works by loading the data in items.txt,
    removing the data in exceptions.txt (if any), and then applying the transformations
    in transform_config.json (if any). If there are nested lookup lists, they will be
    loaded and treated as if they are on items.txt.

    Args:
        path: The path.

    Returns:
        The raw items, as a set of strings.
    """

    items = optional_load_items(path / "items.txt")
    exceptions = optional_load_items(path / "exceptions.txt")

    sub_list_dirs = list(path.glob("lst_*"))

    if items is None:

        if len(sub_list_dirs) == 0:
            raise RuntimeError(
                f"Cannot import lookup list {path}, did not find "
                f"items.txt or any sublists."
            )

        items = set()

    if exceptions is not None:
        items -= exceptions

    for sub_list_dir in sub_list_dirs:
        items = items.union(load_raw_itemset(sub_list_dir))

    transform_config = optional_load_json(path / "transform.json")

    if transform_config is not None:
        items = apply_transform(items, transform_config)

    return items


def load_raw_itemsets(base_path: Path, subdirs: list[str]) -> dict[str, set[str]]:
    """
    Loads one or more raw itemsets. Automatically parses its name from the folder name.

    Args:
        base_path: The base path containing the lists.
        subdirs: The lists to load.

    Returns:
        The raw itemsetes, represented as a dictionary mapping the name of the
        lookup list to a set of strings.
    """

    lists = {}

    for lst in subdirs:
        name = lst.split("/")[-1]
        name = name.removeprefix("lst_")
        lists[name] = load_raw_itemset(base_path / _SRC_SUBDIR / lst)

    return lists


def validate_lookup_struct_cache(
    cache: dict, base_path: Path, deduce_version: str
) -> bool:
    """
    Validates lookup structure data loaded from cache. Invalidates when changes in
    source are detected, or when deduce version doesn't match.

    Args:
        cache: The data loaded from the pickled cache.
        base_path: The base path to check for changed files.
        deduce_version: The current deduce version.

    Returns:
        True when the lookup structure data is valid, False otherwise.
    """

    if cache["deduce_version"] != deduce_version:
        return False

    src_path = base_path / _SRC_SUBDIR

    for file in src_path.glob("**"):

        if datetime.fromtimestamp(os.stat(file).st_mtime) > datetime.fromisoformat(
            cache["saved_datetime"]
        ):
            return False

    return True


def load_lookup_structs_from_cache(
    base_path: Path, deduce_version: str
) -> Optional[dd.ds.DsCollection]:
    """
    Loads lookup struct data from cache. Returns None when no cache is present, or when
    it's invalid.

    Args:
        base_path: The base path where to look for the cache.
        deduce_version: The current deduce version, used to validate.

    Returns:
        A DsCollection if present and valid, None otherwise.
    """

    cache_file = base_path / _CACHE_SUBDIR / _CACHE_FILE

    try:
        with open(cache_file, "rb") as file:
            cache = pickle.load(file)
    except FileNotFoundError:
        return None

    if validate_lookup_struct_cache(
        cache=cache, base_path=base_path, deduce_version=deduce_version
    ):
        return cache["lookup_structs"]

    return None


def cache_lookup_structs(
    lookup_structs: dd.ds.DsCollection, base_path: Path, deduce_version: str
) -> None:
    """
    Saves lookup structs to cache, along with some metadata.

    Args:
        lookup_structs: The lookup structures to cache.
        base_path: The base path for lookup structures.
        deduce_version: The current deduce version.
    """

    cache_file = base_path / _CACHE_SUBDIR / _CACHE_FILE

    cache = {
        "deduce_version": deduce_version,
        "saved_datetime": str(datetime.now()),
        "lookup_structs": lookup_structs,
    }

    with open(cache_file, "wb") as file:
        pickle.dump(cache, file)


def get_lookup_structs(
    lookup_path: Path,
    tokenizer: Tokenizer,
    deduce_version: str,
    all_lists: list,
    build: bool = False,
    save_cache: bool = True,
) -> dd.ds.DsCollection:
    """
    Loads all lookup structures, and handles caching.
    Args:
        lookup_path: The base path for lookup sets.
        tokenizer: The tokenizer, used to create sequences for LookupTrie
        deduce_version: The current deduce version, used to validate cache.
        all_lists: The list of lookup tables that must be used.
        build: Whether to do a full build, even when cache is present and valid.
        save_cache: Whether to save to cache. Only used after building.

    Returns: The lookup structures.

    """

    if not build:

        lookup_structs = load_lookup_structs_from_cache(lookup_path, deduce_version)

        if lookup_structs is not None:
            return lookup_structs

    logging.info(
        "Please wait 1-2 minutes while lookup data structures are being "
        "loaded and built. This process is only triggered for new installs, "
        "when the source lookup lists have changed on disk, or when "
        "explicitly triggered with Deduce(build_lookup_structs=True)."
    )

    lookup_structs = DeprecatedDsCollection(
        deprecated_items={
            "prefixes": "prefix",
            "first_names": "first_name",
            "first_name_exceptions": None,
            "interfixes": "interfix",
            "interfix_surnames": "interfix_surname",
            "surnames": "surname",
            "surname_exceptions": None,
            "streets": "street",
            "placenames": "placename",
            "hospitals": "hospital",
            "healthcare_institutions": "healthcare_institution",
        }
    )

    base_items = load_raw_itemsets(base_path=lookup_path, subdirs=all_lists)

    defaults = (
        set(base_items.keys())
        - set(_LOOKUP_SET_LOADERS.keys())
        - set(_LOOKUP_TRIE_LOADERS.keys())
    )

    for name in defaults:
        lookup_set = dd.ds.LookupSet()
        lookup_set.add_items_from_iterable(base_items[name])
        lookup_structs[name] = lookup_set

    for name, set_init_function in _LOOKUP_SET_LOADERS.items():
        lookup_structs[name] = set_init_function(base_items)

    for name, trie_init_function in _LOOKUP_TRIE_LOADERS.items():
        lookup_structs[name] = trie_init_function(base_items, tokenizer)

    if save_cache:
        cache_lookup_structs(
            lookup_structs=lookup_structs,
            base_path=lookup_path,
            deduce_version=deduce_version,
        )

    return lookup_structs
