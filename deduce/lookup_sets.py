import os
from pathlib import Path

import docdeid as dd

from deduce.str.processor import (
    Acronimify,
    FilterBasedOnLookupSet,
    RemoveValues,
    TakeLastToken,
    TitleCase,
    UpperCaseFirstChar,
)

data_path = Path(os.path.dirname(__file__)).parent / "data" / "lookup_lists"


def _get_prefixes() -> dd.ds.LookupSet:
    """Get prefixes LookupSet (e.g. 'dr', 'mw')"""

    prefixes = dd.ds.LookupSet()

    prefixes.add_items_from_file(os.path.join(data_path, "prefixes.txt"))
    prefixes.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])

    return prefixes


def _get_first_names() -> dd.ds.LookupSet:
    """Get first names LookupSet."""

    first_names = dd.ds.LookupSet()

    first_names.add_items_from_file(
        os.path.join(data_path, "first_names.txt"),
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return first_names


def _get_first_name_exceptions() -> dd.ds.LookupSet:
    """Get first name exceptions."""

    first_name_exceptions = dd.ds.LookupSet()

    first_name_exceptions.add_items_from_file(
        os.path.join(data_path, "first_name_exceptions.txt"),
    )

    return first_name_exceptions


def _get_interfixes() -> dd.ds.LookupSet:
    """Get interfixes LookupSet ('van der', etc.)"""

    interfixes = dd.ds.LookupSet()

    interfixes.add_items_from_file(os.path.join(data_path, "interfixes.txt"))
    interfixes.add_items_from_self(cleaning_pipeline=[UpperCaseFirstChar()])
    interfixes.add_items_from_self(cleaning_pipeline=[TitleCase()])
    interfixes.remove_items_from_iterable(["V."])

    return interfixes


def _get_interfix_surnames() -> dd.ds.LookupSet:
    """Get interfix surnames LookupSet (e.g. 'Jong' for 'de Jong')"""

    interfix_surnames = dd.ds.LookupSet()

    interfix_surnames.add_items_from_file(
        os.path.join(data_path, "interfix_surnames.txt"),
        cleaning_pipeline=[TakeLastToken()],
    )

    return interfix_surnames


def _get_surnames() -> dd.ds.LookupSet:
    """Get surnames LookupSet."""

    surnames = dd.ds.LookupSet()

    surnames.add_items_from_file(
        os.path.join(data_path, "surnames.txt"),
        cleaning_pipeline=[dd.str.FilterByLength(min_len=2)],
    )

    return surnames


def _get_surname_exceptions() -> dd.ds.LookupSet:
    """Get surname exceptions."""

    surname_exceptions = dd.ds.LookupSet()

    surname_exceptions.add_items_from_file(
        os.path.join(data_path, "surname_exceptions.txt"),
    )

    return surname_exceptions


def _get_residences() -> dd.ds.LookupSet:
    """Get residences LookupSet."""

    residences = dd.ds.LookupSet()
    residences.add_items_from_file(
        file_path=os.path.join(data_path, "residences.txt"),
        cleaning_pipeline=[dd.str.ReplaceValueRegexp(r"\(.+\)", ""), dd.str.StripString()],
    )

    residences.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceValue("-", " ")])

    residences.add_items_from_self(
        cleaning_pipeline=[FilterBasedOnLookupSet(filter_set=get_whitelist(), case_sensitive=False)],
        replace=True,
    )

    return residences


def get_institutions() -> dd.ds.LookupSet:
    """Get institutions LookupSet."""

    institutions_raw = dd.ds.LookupSet()
    institutions_raw.add_items_from_file(
        os.path.join(data_path, "institutions.txt"),
        cleaning_pipeline=[dd.str.FilterByLength(min_len=3), dd.str.LowercaseString()],
    )

    institutions = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])
    institutions.add_items_from_iterable(institutions_raw, cleaning_pipeline=[dd.str.StripString()])

    institutions.add_items_from_iterable(
        institutions_raw,
        cleaning_pipeline=[
            RemoveValues(filter_values=["dr.", "der", "van", "de", "het", "'t", "in", "d'"]),
            dd.str.StripString(),
        ],
    )

    institutions.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceValue(".", ""), dd.str.StripString()])

    institutions.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceValue("st ", "sint ")])

    institutions.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceValue("st. ", "sint ")])

    institutions.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceValue("ziekenhuis", "zkh")])

    institutions.add_items_from_self(
        cleaning_pipeline=[dd.str.LowercaseString(), Acronimify(), dd.str.FilterByLength(min_len=3)]
    )

    institutions = institutions - get_whitelist()

    return institutions


def _get_top_terms() -> dd.ds.LookupSet:

    top1000 = dd.ds.LookupSet()
    top1000.add_items_from_file(
        os.path.join(data_path, "top_1000_terms.txt"),
    )

    surnames_lowercase = dd.ds.LookupSet()
    surnames_lowercase.add_items_from_file(
        os.path.join(data_path, "surnames.txt"),
        cleaning_pipeline=[
            dd.str.LowercaseString(),
            dd.str.FilterByLength(min_len=2),
        ],
    )

    top1000 = top1000 - surnames_lowercase

    return top1000


def get_whitelist() -> dd.ds.LookupSet:
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
        "residences": _get_residences,
        "institutions": get_institutions,
        "whitelist": get_whitelist,
    }

    for name, init_function in lookup_set_mapping.items():
        lookup_sets[name] = init_function()

    return lookup_sets
