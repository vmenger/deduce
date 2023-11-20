import os
from pathlib import Path

import docdeid as dd

from deduce.str.processor import (
    FilterBasedOnLookupSet,
    TitleCase,
    UpperCase,
    UpperCaseFirstChar,
)

data_path = Path(os.path.dirname(__file__)).parent / "deduce-data" / "lookup_lists"


def _get_prefixes() -> dd.ds.LookupSet:
    """Get prefixes LookupSet (e.g. 'dr', 'mw')"""

    prefixes = dd.ds.LookupSet()

    prefixes.add_items_from_file(os.path.join(data_path, "names", "prefixes.txt"))
    prefixes.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])

    return prefixes


def _get_first_names() -> dd.ds.LookupSet:
    """Get first names LookupSet."""

    first_names = dd.ds.LookupSet()

    first_names.add_items_from_file(
        os.path.join(data_path, "names", "first_names.txt"),
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return first_names


def _get_first_name_exceptions() -> dd.ds.LookupSet:
    """Get first name exceptions."""

    first_name_exceptions = dd.ds.LookupSet()

    first_name_exceptions.add_items_from_file(
        os.path.join(data_path, "names", "first_name_exceptions.txt"),
    )

    return first_name_exceptions


def _get_interfixes() -> dd.ds.LookupSet:
    """Get interfixes LookupSet ('van der', etc.)"""

    interfixes = dd.ds.LookupSet()

    interfixes.add_items_from_file(os.path.join(data_path, "names", "interfixes.txt"))
    interfixes.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])
    interfixes.add_items_from_self(cleaning_pipeline=[TitleCase()])
    interfixes.remove_items_from_iterable(["V."])

    return interfixes


def _get_interfix_surnames() -> dd.ds.LookupSet:
    """Get interfix surnames LookupSet (e.g. 'Jong' for 'de Jong')"""

    interfix_surnames = dd.ds.LookupSet()

    interfix_surnames.add_items_from_file(
        os.path.join(data_path, "names", "interfix_surnames.txt"),
    )

    interfix_surname_exceptions = dd.ds.LookupSet()

    interfix_surname_exceptions.add_items_from_file(
        os.path.join(data_path, "names", "interfix_surname_exceptions.txt")
    )

    interfix_surnames.remove_items_from_iterable(interfix_surname_exceptions)

    return interfix_surnames


def _get_surnames() -> dd.ds.LookupSet:
    """Get surnames LookupSet."""

    surnames = dd.ds.LookupSet()

    surnames.add_items_from_file(
        os.path.join(data_path, "names", "surnames.txt"),
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return surnames


def _get_surname_exceptions() -> dd.ds.LookupSet:
    """Get surname exceptions."""

    surname_exceptions = dd.ds.LookupSet()

    surname_exceptions.add_items_from_file(
        os.path.join(data_path, "names", "surname_exceptions.txt"),
    )

    return surname_exceptions


def _get_streets() -> dd.ds.LookupSet:
    """Get streets lookupset."""

    streets = dd.ds.LookupSet()

    streets.add_items_from_file(
        file_path=os.path.join(data_path, "locations", "streets", "streets_long.txt"),
        cleaning_pipeline=[
            dd.str.StripString(),
            dd.str.FilterByLength(min_len=4),
        ],
    )

    streets.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()])

    return streets


def _get_placenames() -> dd.ds.LookupSet:
    """Get place names LookupSet."""

    placenames = dd.ds.LookupSet()

    placenames.add_items_from_file(
        file_path=os.path.join(data_path, "locations", "placenames_long.txt"),
        cleaning_pipeline=[
            dd.str.StripString(),
        ],
    )

    placenames.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()]
    )

    placenames.add_items_from_self(
        cleaning_pipeline=[
            dd.str.ReplaceValue("(", ""),
            dd.str.ReplaceValue(")", ""),
            dd.str.ReplaceValue("  ", " "),
        ]
    )

    placenames.add_items_from_self(cleaning_pipeline=[UpperCase()])

    placenames.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(filter_set=_get_whitelist(), case_sensitive=False),
        ],
        replace=True,
    )

    return placenames


def _get_hospitals() -> dd.ds.LookupSet:

    hospitals = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])

    hospitals.add_items_from_file(
        os.path.join(data_path, "institutions", "hospital_long.txt")
    )

    hospitals.add_items_from_file(
        os.path.join(data_path, "institutions", "hospital_abbr.txt")
    )

    hospitals.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )

    return hospitals


def _get_institutions() -> dd.ds.LookupSet:
    """Get institutions LookupSet."""

    institutions = dd.ds.LookupSet()
    institutions.add_items_from_file(
        os.path.join(data_path, "institutions", "healthcare_institutions_long.txt"),
        cleaning_pipeline=[dd.str.StripString(), dd.str.FilterByLength(min_len=4)],
    )

    institutions.add_items_from_self(cleaning_pipeline=[UpperCase()])

    institutions.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()],
    )
    institutions = institutions - _get_whitelist()

    return institutions


def _get_top_terms() -> dd.ds.LookupSet:
    top1000 = dd.ds.LookupSet()
    top1000.add_items_from_file(
        os.path.join(data_path, "top_1000_terms.txt"),
    )

    surnames_lowercase = dd.ds.LookupSet()
    surnames_lowercase.add_items_from_file(
        os.path.join(data_path, "names", "surnames.txt"),
        cleaning_pipeline=[
            dd.str.LowercaseString(),
            dd.str.FilterByLength(min_len=2),
        ],
    )

    top1000 = top1000 - surnames_lowercase

    return top1000


def _get_whitelist() -> dd.ds.LookupSet:
    """
    Get whitelist LookupSet.

    Composed of medical terms, top 1000 frequent words (except surnames), and stopwords.
    Returns:
    """
    med_terms = dd.ds.LookupSet()
    med_terms.add_items_from_file(
        os.path.join(data_path, "medical_terms.txt"),
    )

    top1000 = _get_top_terms()

    stopwords = dd.ds.LookupSet()
    stopwords.add_items_from_file(os.path.join(data_path, "stop_words.txt"))

    whitelist = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])
    whitelist.add_items_from_iterable(
        med_terms + top1000 + stopwords,
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return whitelist


def get_lookup_sets() -> dd.ds.DsCollection:
    """
    Get all lookupsets.

    Returns:
        A DsCollection with all lookup sets.
    """

    lookup_sets = dd.ds.DsCollection()

    lookup_set_mapping = {
        "prefixes": _get_prefixes,
        "first_names": _get_first_names,
        "first_name_exceptions": _get_first_name_exceptions,
        "interfixes": _get_interfixes,
        "interfix_surnames": _get_interfix_surnames,
        "surnames": _get_surnames,
        "surname_exceptions": _get_surname_exceptions,
        "streets": _get_streets,
        "placenames": _get_placenames,
        "hospitals": _get_hospitals,
        "healthcare_institutions": _get_institutions,
        "whitelist": _get_whitelist,
    }

    for name, init_function in lookup_set_mapping.items():
        lookup_sets[name] = init_function()

    return lookup_sets
