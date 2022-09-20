""" This module contains all list reading functionality """
import os

from deduce.str.processor import (
    Acronimify,
    FilterBasedOnLookupList,
    RemoveValues,
    TakeLastToken,
)
from docdeid.ds import DsCollection, LookupList
from docdeid.str.processor import (
    FilterByLength,
    LowercaseString,
    ReplaceValue,
    ReplaceValueRegexp,
    StripString,
)

data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data")


def _get_first_names_lookuplist():

    first_names = LookupList()

    first_names.add_items_from_file(
        os.path.join(data_path, "voornaam.lst"),
        cleaning_pipeline=[FilterByLength(min_len=2)],
    )

    return first_names


def _get_surnames_lookuplist():

    surnames = LookupList()

    surnames.add_items_from_file(
        os.path.join(data_path, "achternaam.lst"),
        strip_lines=False,
        cleaning_pipeline=[StripString(), FilterByLength(min_len=2)],
    )

    return surnames


def _get_interfixes_lookuplist():
    """Interfixes, such as 'van der', etc"""

    interfixes = LookupList()

    interfixes.add_items_from_file(os.path.join(data_path, "voorvoegsel.lst"))

    return interfixes


def _get_interfix_surnames_lookuplist():
    """Interfix surnames, such as 'Jong' for 'de Jong'"""

    interfix_surnames = LookupList()

    interfix_surnames.add_items_from_file(
        os.path.join(data_path, "achternaammetvv.lst"),
        cleaning_pipeline=[TakeLastToken()],
    )

    return interfix_surnames


def _get_prefixes_lookuplist():

    prefixes = LookupList()

    prefixes.add_items_from_file(os.path.join(data_path, "prefix.lst"))

    return prefixes


def _get_whitelist_lookuplist():

    med_terms = LookupList()
    med_terms.add_items_from_file(
        os.path.join(data_path, "medischeterm.lst"),
        encoding="latin-1",
    )

    top1000 = LookupList()
    top1000.add_items_from_file(
        os.path.join(data_path, "top1000.lst"),
        encoding="latin-1",
    )

    surnames_lowercase = LookupList()
    surnames_lowercase.add_items_from_file(
        os.path.join(data_path, "achternaam.lst"),
        strip_lines=False,
        cleaning_pipeline=[
            LowercaseString(),
            StripString(),
            FilterByLength(min_len=2),
        ],
    )

    top1000 = top1000 - surnames_lowercase

    stopwords = LookupList()
    stopwords.add_items_from_file(os.path.join(data_path, "stopwoord.lst"))

    whitelist = LookupList()
    whitelist.add_items_from_iterable(
        med_terms + top1000 + stopwords,
        cleaning_pipeline=[LowercaseString(), FilterByLength(min_len=2)],
    )

    # return whitelist
    return whitelist


def _get_institutions_lookuplist():

    institutions_raw = LookupList()
    institutions_raw.add_items_from_file(
        os.path.join(data_path, "instellingen.lst"),
        cleaning_pipeline=[FilterByLength(min_len=3)],
    )

    institutions = LookupList()
    institutions.add_items_from_iterable(
        institutions_raw, cleaning_pipeline=[LowercaseString(), StripString()]
    )

    institutions.add_items_from_iterable(
        institutions_raw,
        cleaning_pipeline=[
            LowercaseString(),
            RemoveValues(
                filter_values=["dr.", "der", "van", "de", "het", "'t", "in", "d'"]
            ),
            StripString(),
        ],
    )

    institutions.add_items_from_self(
        cleaning_pipeline=[ReplaceValue(".", ""), StripString()]
    )

    institutions.add_items_from_self(cleaning_pipeline=[ReplaceValue("st ", "sint ")])

    institutions.add_items_from_self(cleaning_pipeline=[ReplaceValue("st. ", "sint ")])

    institutions.add_items_from_self(
        cleaning_pipeline=[ReplaceValue("ziekenhuis", "zkh")]
    )

    institutions.add_items_from_self(
        cleaning_pipeline=[LowercaseString(), Acronimify(min_length=3)]
    )

    institutions = institutions - _get_whitelist_lookuplist()

    return institutions


def _get_residences_lookuplist():

    residences = LookupList()
    residences.add_items_from_file(
        file=os.path.join(data_path, "woonplaats.lst"),
        encoding="utf-8",
        cleaning_pipeline=[ReplaceValueRegexp(r"\(.+\)", ""), StripString()],
    )

    residences.add_items_from_self(cleaning_pipeline=[ReplaceValue("-", " ")])

    residences.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupList(
                filter_list=_get_whitelist_lookuplist(), case_sensitive=False
            )
        ],
        replace=True,
    )

    return residences


def get_lookup_lists():
    lookup_lists = DsCollection()

    lookup_list_mapping = {
        "first_names": _get_first_names_lookuplist,
        "surnames": _get_surnames_lookuplist,
        "interfixes": _get_interfixes_lookuplist,
        "interfix_surnames": _get_interfix_surnames_lookuplist,
        "prefixes": _get_prefixes_lookuplist,
        "whitelist": _get_whitelist_lookuplist,
        "institutions": _get_institutions_lookuplist,
        "residences": _get_residences_lookuplist,
    }

    for name, init_function in lookup_list_mapping.items():
        lookup_lists[name] = init_function()

    return lookup_lists
