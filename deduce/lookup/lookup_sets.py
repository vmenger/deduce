import os

from docdeid.ds import DsCollection, LookupSet
from docdeid.str.processor import (
    FilterByLength,
    LowercaseString,
    ReplaceValue,
    ReplaceValueRegexp,
    StripString,
)

from deduce.str.processor import (
    Acronimify,
    FilterBasedOnLookupSet,
    RemoveValues,
    TakeLastToken,
)

data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data")


def _get_first_names_lookup_set() -> LookupSet:

    first_names = LookupSet()

    first_names.add_items_from_file(
        os.path.join(data_path, "voornaam.lst"),
        cleaning_pipeline=[FilterByLength(min_len=2)],
    )

    return first_names


def _get_surnames_lookup_set() -> LookupSet:

    surnames = LookupSet()

    surnames.add_items_from_file(
        os.path.join(data_path, "achternaam.lst"),
        cleaning_pipeline=[FilterByLength(min_len=2)],
    )

    return surnames


def _get_interfixes_lookup_set() -> LookupSet:
    """Interfixes, such as 'van der', etc"""

    interfixes = LookupSet()

    interfixes.add_items_from_file(os.path.join(data_path, "voorvoegsel.lst"))

    return interfixes


def _get_interfix_surnames_lookup_set() -> LookupSet:
    """Interfix surnames, such as 'Jong' for 'de Jong'"""

    interfix_surnames = LookupSet()

    interfix_surnames.add_items_from_file(
        os.path.join(data_path, "achternaammetvv.lst"),
        cleaning_pipeline=[TakeLastToken()],
    )

    return interfix_surnames


def _get_prefixes_lookup_set() -> LookupSet:

    prefixes = LookupSet()

    prefixes.add_items_from_file(os.path.join(data_path, "prefix.lst"))

    return prefixes


def _get_whitelist_lookup_set() -> LookupSet:

    med_terms = LookupSet()
    med_terms.add_items_from_file(
        os.path.join(data_path, "medischeterm.lst"),
        encoding="latin-1",
    )

    top1000 = LookupSet()
    top1000.add_items_from_file(
        os.path.join(data_path, "top1000.lst"),
        encoding="latin-1",
    )

    surnames_lowercase = LookupSet()
    surnames_lowercase.add_items_from_file(
        os.path.join(data_path, "achternaam.lst"),
        cleaning_pipeline=[
            LowercaseString(),
            FilterByLength(min_len=2),
        ],
    )

    top1000 = top1000 - surnames_lowercase

    stopwords = LookupSet()
    stopwords.add_items_from_file(os.path.join(data_path, "stopwoord.lst"))

    whitelist = LookupSet(matching_pipeline=[LowercaseString()])
    whitelist.add_items_from_iterable(
        med_terms + top1000 + stopwords,
        cleaning_pipeline=[FilterByLength(min_len=2)],
    )

    return whitelist


def _get_institutions_lookup_set() -> LookupSet:

    institutions_raw = LookupSet()
    institutions_raw.add_items_from_file(
        os.path.join(data_path, "instellingen.lst"),
        cleaning_pipeline=[FilterByLength(min_len=3), LowercaseString()],
    )

    institutions = LookupSet(matching_pipeline=[LowercaseString()])
    institutions.add_items_from_iterable(institutions_raw, cleaning_pipeline=[StripString()])

    institutions.add_items_from_iterable(
        institutions_raw,
        cleaning_pipeline=[
            RemoveValues(filter_values=["dr.", "der", "van", "de", "het", "'t", "in", "d'"]),
            StripString(),
        ],
    )

    institutions.add_items_from_self(cleaning_pipeline=[ReplaceValue(".", ""), StripString()])

    institutions.add_items_from_self(cleaning_pipeline=[ReplaceValue("st ", "sint ")])

    institutions.add_items_from_self(cleaning_pipeline=[ReplaceValue("st. ", "sint ")])

    institutions.add_items_from_self(cleaning_pipeline=[ReplaceValue("ziekenhuis", "zkh")])

    institutions.add_items_from_self(cleaning_pipeline=[LowercaseString(), Acronimify(), FilterByLength(min_len=3)])

    institutions = institutions - _get_whitelist_lookup_set()

    return institutions


def _get_residences_lookup_set() -> LookupSet:

    residences = LookupSet()
    residences.add_items_from_file(
        file=os.path.join(data_path, "woonplaats.lst"),
        encoding="utf-8",
        cleaning_pipeline=[ReplaceValueRegexp(r"\(.+\)", ""), StripString()],
    )

    residences.add_items_from_self(cleaning_pipeline=[ReplaceValue("-", " ")])

    residences.add_items_from_self(
        cleaning_pipeline=[FilterBasedOnLookupSet(filter_set=_get_whitelist_lookup_set(), case_sensitive=False)],
        replace=True,
    )

    return residences


def get_lookup_sets() -> DsCollection:
    lookup_sets = DsCollection()

    lookup_set_mapping = {
        "first_names": _get_first_names_lookup_set,
        "surnames": _get_surnames_lookup_set,
        "interfixes": _get_interfixes_lookup_set,
        "interfix_surnames": _get_interfix_surnames_lookup_set,
        "prefixes": _get_prefixes_lookup_set,
        "whitelist": _get_whitelist_lookup_set,
        "institutions": _get_institutions_lookup_set,
        "residences": _get_residences_lookup_set,
    }

    for name, init_function in lookup_set_mapping.items():
        lookup_sets[name] = init_function()

    return lookup_sets
