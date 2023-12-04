import glob
import json
import os
from typing import Optional

import docdeid as dd

from deduce.data.lookup_lists.src import _all_lists
from deduce.str.processor import (
    FilterBasedOnLookupSet,
    TitleCase,
    UpperCase,
    UpperCaseFirstChar,
)
from deduce.utils import str_variations


def safe_load_items(path: str) -> Optional[set[str]]:

    try:
        with open(path, "r") as file:
            items = {line.strip() for line in file.readlines()}
    except FileNotFoundError as e:
        return None

    return items


def safe_load_json(path: str) -> Optional[dict]:

    try:
        with open(path, "r") as file:
            data = json.load(file)
    except FileNotFoundError as e:
        return None

    return data


def apply_transform(items: set[str], transform: dict) -> set[str]:

    strip_lines = transform.get("strip_lines", True)
    transforms = transform.get("transforms", {})

    for name, transform in transforms.items():

        to_add = []

        for item in items:
            to_add += str_variations(item, transform)

        items.update(to_add)

    if strip_lines:
        items = {i.strip() for i in items}

    return items


def load_base_items(path: str) -> set[str]:

    items = safe_load_items(path + "items.txt")
    exceptions = safe_load_items(path + "exceptions.txt")

    if items is None:
        raise RuntimeError(f"Cannot import lookup list {path}, no items.txt found.")

    if exceptions is not None:
        items -= exceptions

    for dir in glob.glob(path + "lst_*"):
        items = items.union(load_base_items(dir + "/"))

    transform = safe_load_json(path + "transform.json")

    if transform is not None:
        items = apply_transform(items, transform)

    return items


def load_lists(path: str) -> dict[str, set[str]]:

    lists = dict()

    for lst in _all_lists:

        name = lst.split("/")[-1]
        name = name.removeprefix("lst_")

        lists[name] = load_base_items(str(path + lst) + "/")

    return lists


def _get_prefix(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Get prefix LookupSet (e.g. 'dr', 'mw')"""

    prefix = dd.ds.LookupSet()

    prefix.add_items_from_iterable(base_items['prefix'])
    prefix.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])

    return prefix


def _get_first_name(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Get first name LookupSet."""

    fisrt_name = dd.ds.LookupSet()

    fisrt_name.add_items_from_iterable(
        base_items['first_name'],
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    fisrt_name.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(filter_set=_get_whitelist(base_items), case_sensitive=False),
        ],
        replace=True,
    )

    return fisrt_name


def _get_interfix(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Get interfix LookupSet ('van der', etc.)"""

    interfix = dd.ds.LookupSet()

    interfix.add_items_from_iterable(base_items['interfix'])
    interfix.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])
    interfix.add_items_from_self(cleaning_pipeline=[TitleCase()])
    interfix.remove_items_from_iterable(["V."])

    return interfix


def _get_surname(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Get surname LookupSet."""

    surname = dd.ds.LookupSet()

    surname.add_items_from_iterable(
        base_items['surname'],
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    surname.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(filter_set=_get_whitelist(base_items), case_sensitive=False),
        ],
        replace=True,
    )

    return surname


def _get_street(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Get street lookupset."""

    street = dd.ds.LookupSet()

    street.add_items_from_iterable(
        base_items['street'],
        cleaning_pipeline=[
            dd.str.StripString(),
            dd.str.FilterByLength(min_len=4),
        ],
    )

    street.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()])

    return street


def _get_placename(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Get placename LookupSet."""

    placename = dd.ds.LookupSet()

    placename.add_items_from_iterable(
        base_items['placename'],
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
            FilterBasedOnLookupSet(filter_set=_get_whitelist(base_items), case_sensitive=False),
        ],
        replace=True,
    )

    return placename


def _get_hospital(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:

    hospital = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])

    hospital.add_items_from_iterable(
        base_items['hospital']
    )

    hospital.add_items_from_iterable(
        base_items['hospital_abbr']
    )

    hospital.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )

    return hospital


def _get_institution(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """Get institution LookupSet."""

    institution = dd.ds.LookupSet()
    institution.add_items_from_iterable(
        base_items['healthcare_institution'],
        cleaning_pipeline=[dd.str.StripString(), dd.str.FilterByLength(min_len=4)],
    )

    institution.add_items_from_self(cleaning_pipeline=[UpperCase()])

    institution.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )
    institution = institution - _get_whitelist(base_items)

    return institution


def _get_common_word(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:

    common_word = dd.ds.LookupSet()
    common_word.add_items_from_iterable(
        base_items['common_word'],
    )

    surnames_lowercase = dd.ds.LookupSet()
    surnames_lowercase.add_items_from_iterable(
        base_items['surname'],
        cleaning_pipeline=[
            dd.str.LowercaseString(),
            dd.str.FilterByLength(min_len=2),
        ],
    )

    common_word -= surnames_lowercase

    return common_word


def _get_whitelist(base_items: dict[str, set[str]]) -> dd.ds.LookupSet:
    """
    Get whitelist LookupSet.

    Composed of medical terms, top 1000 frequent words (except surnames), and stopwords.
    Returns:
    """
    medical_term = dd.ds.LookupSet()

    medical_term.add_items_from_iterable(
        base_items['medical_term'],
    )

    common_word = _get_common_word(base_items)

    stop_word = dd.ds.LookupSet()
    stop_word.add_items_from_iterable(base_items['stop_word'])

    whitelist = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])
    whitelist.add_items_from_iterable(
        medical_term + common_word + stop_word,
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return whitelist


def _default_loader(name, lists: dict[str, set[str]]) -> dd.ds.LookupSet:

    lookup_set = dd.ds.LookupSet()
    lookup_set.add_items_from_iterable(lists[name])
    return lookup_set


def get_lookup_sets(path: str) -> dd.ds.DsCollection:
    """
    Get all lookupsets.

    Returns:
        A DsCollection with all lookup sets.
    """

    lookup_sets = dd.ds.DsCollection()
    base_items = load_lists(path=path)

    lookup_set_loaders = {
        "prefix": _get_prefix,
        "first_name": _get_first_name,
        "interfix": _get_interfix,
        "surname": _get_surname,
        "street": _get_street,
        "placename": _get_placename,
        "hospital": _get_hospital,
        "healthcare_institution": _get_institution,
        "whitelist": _get_whitelist,
    }

    defaults = set(base_items.keys()) - set(lookup_set_loaders.keys())

    for name in defaults:
        lookup_sets[name] = _default_loader(name, base_items)

    for name, init_function in lookup_set_loaders.items():
        lookup_sets[name] = init_function(base_items)

    return lookup_sets
