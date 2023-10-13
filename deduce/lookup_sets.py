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
    UpperCase,
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


def _get_streets() -> dd.ds.LookupSet:
    """Get streets lookupset."""

    street_exceptions = dd.ds.LookupSet()

    street_exceptions.add_items_from_file(
        file_path=os.path.join(data_path, "street_exceptions.txt")
    )

    streets = dd.ds.LookupSet()

    streets.add_items_from_file(
        file_path=os.path.join(data_path, "streets.txt"),
        cleaning_pipeline=[
            dd.str.StripString(),
            dd.str.FilterByLength(min_len=4),
        ],
    )

    streets.remove_items_from_iterable(street_exceptions)

    streets.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()])

    prefix_mapping = {
        r"\bAbraham\b": ["Abraham", "Abr.", "abr."],
        r"\bAdmiraal\b": ["Admiraal", "Adm.", "adm."],
        r"\bAlbert\b": ["Albert", "Alb.", "alb."],
        r"\bBurgemeester\b": ["Burgemeester", "Burg.", "burg."],
        r"\bChris\b": ["Chris", "Chr.", "chr."],
        r"\bCommissaris\b": ["Commissaris", "Comm.", "comm."],
        r"\bDominee\b": ["Dominee", "Ds.", "ds."],
        r"\bDoctor\b": ["Doctor", "Dr.", "dr."],
        r"\bDokter\b": ["Dokter", "Dr.", "dr."],
        r"\bDoctorandus\b": ["Doctorandus", "Drs.", "drs."],
        r"\bFamilie\b": ["Familie", "Fam.", "fam."],
        r"\bGebroeders\b": ["Gebroeders", "Gebr.", "gebr.", "Gebrs.", "gebrs."],
        r"\bGeneraal\b": ["Generaal", "Gen.", "gen."],
        r"\bHertog\b": ["Hertog", "Hert.", "hert."],
        r"\bIngenieur\b": ["Ingenieur", "Ir.", "ir.", "Ing.", "ing."],
        r"\bJacobus\b": ["Jacobus", "Jac.", "jac."],
        r"\bJacob\b": ["Jacobus", "Jac.", "jac."],
        r"\bJacqueline\b": ["Jacqueline", "Jacq.", "jacq."],
        r"\bJonkhkeer\b": ["Jonkhkeer", "Jhr.", "jhr."],
        r"\bJonkvrouw\b": ["Jonkvrouw", "Jkvr.", "jkvr."],
        r"\bJohan\b": ["Johan", "Joh.", "joh."],
        r"\bKardinaal\b": ["Kardinaal", "Kard.", "kard."],
        r"\bKolonel\b": ["Kolonel", "Kol.", "kol."],
        r"\bKoningin\b": ["Koningin", "Kon.", "kon."],
        r"\bKoning\b": ["Koning", "Kon.", "kon."],
        r"\bMajoor\b": ["Majoor", "Maj.", "maj."],
        r"\bMevrouw\b": ["Mevrouw", "Mevr.", "mevr."],
        r"\bMinister\b": ["Minister", "Min.", "min."],
        r"\bMeester\b": ["Meester", "Mr.", "mr."],
        r"\bMonseigneur\b": ["Monseigneur", "Mgr.", "mgr."],
        r"\bPrinses\b": ["Prinses", "Pr.", "pr."],
        r"\bProfessor\b": ["Professor", "Prof.", "prof."],
        r"\bRector\b": ["Rector", "Rect.", "rect."],
        r"\bSecretaris\b": ["Secretaris", "Secr.", "secr."],
        r"\bSenior\b": ["Senior", "Sr.", "sr."],
        r"\bSint\b": ["Sint", "sint", "St.", "st."],
        r"\bTheo\b": ["Theo", "Th.", "th."],
        r"\bVeldmaarschalk\b": ["Veldmaarschalk", "Veldm.", "Veldm"],
        r"\bVicaris\b": ["Vicaris", "Vic.", "vic."],
        r"\bZuster\b": ["Zuster", "Zr.", "zr."],
    }

    prop_mapping = {
        r"\baan\b": ["Aan", "aan"],
        r"\bachter\b": ["Achter", "achter"],
        r"\band\b": ["And", "and"],
        r"\bbie\b": ["Bie", "bie"],
        r"\bbij\b": ["Bij", "bij"],
        r"\bbinnenzijde\b": ["Binnenzijde", "binnenzijde", "BZ", "Bz", "bz"],
        r"\bbuitenzijde\b": ["Buitenzijde", "buitenzijde", "BZ", "Bz", "bz"],
        r"\bda\b": ["Da", "da"],
        r"\bde\b": ["De", "de"],
        r"\bdel\b": ["Del", "del"],
        r"\bden\b": ["Den", "den"],
        r"\bder\b": ["Der", "der"],
        r"\bdes\b": ["Des", "des"],
        r"\bdi\b": ["Di", "di"],
        r"\bdie\b": ["Die", "die"],
        r"\bdoor\b": ["Door", "door"],
        r"\bdu\b": ["Du", "du"],
        r"\bein\b": ["Ein", "ein"],
        r"\ben\b": ["En", "en"],
        r"\bfan\b": ["Fan", "fan"],
        r"\bge\b": ["Ge", "ge"],
        r"\bgen\b": ["Gen", "gen"],
        r"\bhet\b": ["Het", "het", "'T", "'t", "`T", "`t", "T", "t"],
        r"\bin\b": ["In", "in"],
        r"\bis\b": ["Is", "is"],
        r"\bit\b": ["It", "it", "Het", "het", "'T", "'t", "`T", "`t", "T", "t"],
        r"\bla\b": ["La", "la"],
        r"\blangs\b": ["Langs", "langs"],
        r"\ble\b": ["Le", "le"],
        r"\bnaar\b": ["Naar", "naar"],
        r"\bnabij\b": ["Nabij", "nabij"],
        r"\boan\b": ["Oan", "oan"],
        r"\bof\b": ["Of", "of"],
        r"\bom\b": ["Om", "om"],
        r"\bonder\b": ["Onder", "onder"],
        r"\bop\b": ["Op", "op"],
        r"\bover\b": ["Over", "over"],
        r"\bsur\b": ["Sur", "sur"],
        r"\bte\b": ["Te", "te"],
        r"\bten\b": ["Ten", "ten"],
        r"\bter\b": ["Ter", "ter"],
        r"\btot\b": ["Tot", "tot"],
        r"\btusschen\b": ["Tusschen", "tusschen"],
        r"\btussen\b": ["Tussen", "tussen"],
        r"\but\b": ["Ut", "ut"],
        r"\buten\b": ["Uten", "uten"],
        r"\bvan\b": ["Van", "van"],
        r"\bvon\b": ["Von", "von"],
        r"\bvoor\b": ["Voor", "voor"],
    }

    windrichting_mapping = {
        r"NZ$": ["N.Z.", "N.z.", "n.z.", "Noordzijde", "noordzijde"],
        r"OZ$": ["O.Z.", "O.z.", "o.z.", "Oostzijde", "oostzijde"],
        r"ZZ$": ["Z.Z.", "Z.z.", "z.z.", "Zuidzijde", "zuidzijde"],
        r"WZ$": ["W.Z.", "W.z.", "w.z.", "Westzijde", "westzijde"],
        r"NO$": ["N.O.", "N.o.", "n.o."],
        r"NW$": ["N.W.", "N.w.", "n.w."],
        r"ZO$": ["Z.O.", "Z.o.", "z.o."],
        r"ZW$": ["Z.W.", "Z.w.", "z.w."],
    }

    suffix_mapping = {
        r"dreef$": ["dreef", "drf"],
        r"gracht$": ["gracht", "gr"],
        r"hof$": ["hof", "hf"],
        r"laan$": ["laan", "ln"],
        r"markt$": ["markt", "mrkt"],
        r"pad$": ["pad", "pd"],
        r"park$": ["park", "prk"],
        r"plantsoen$": ["plantsoen", "plnts", "pltsn"],
        r"plein$": ["plein", "pln"],
        r"singel$": ["singel", "sngl"],
        r"steeg$": ["steeg", "stg", "st"],
        r"straat$": ["straat", "str"],
        r"weg$": ["weg", "wg"],
    }

    loc_mapping = {
        r"\bAcker\b": ["Acker", "acker"],
        r"\bAkker\b": ["Akker", "akker"],
        r"\bBoulevard\b": ["Boulevard", "boulevard"],
        r"\bDijk\b": ["Dijk", "dijk"],
        r"\bDreef\b": ["Dreef", "dreef"],
        r"\bDwarsweg\b": ["Dwarsweg", "dwarsweg"],
        r"\bDyk\b": ["Dyk", "dyk"],
        r"\bErf\b": ["Erf", "erf"],
        r"\bHeide\b": ["Heide", "heide"],
        r"\bKade\b": ["Kade", "kade"],
        r"\bKanaal\b": ["Kanaal", "kanaal"],
        r"\bPad\b": ["Pad", "pad"],
        r"\bPark\b": ["Park", "park"],
        r"\bPlantsoen\b": ["Plantsoen", "plantsoen"],
        r"\bPlein\b": ["Plein", "plein"],
        r"\bReed\b": ["Reed", "reed"],
        r"\bRotonde\b": ["Rotonde", "rotonde"],
        r"\bSloot\b": ["Sloot", "sloot"],
        r"\bSluis\b": ["Sluis", "sluis"],
        r"\bSteeg\b": ["Steeg", "steeg"],
        r"\bStraat\b": ["Straat", "straat"],
        r"\bTunnel\b": ["Tunnel", "tunnel"],
        r"\bWal\b": ["Wal", "wal"],
        r"\bWeg\b": ["Weg", "weg"],
        r"\bWei\b": ["Wei", "wei"],
        r"\bWijk\b": ["Wijk", "wijk"],
    }

    punct_mapping = {r"\.": [".", ""], "-": ["-", ""]}

    streets.explode_items_from_self(mapping=prefix_mapping)
    streets.explode_items_from_self(mapping=prop_mapping)
    streets.explode_items_from_self(mapping=windrichting_mapping)
    streets.explode_items_from_self(mapping=suffix_mapping)
    streets.explode_items_from_self(mapping=loc_mapping)
    streets.explode_items_from_self(mapping=punct_mapping)
    return streets


def _get_residences() -> dd.ds.LookupSet:
    """Get residences LookupSet."""

    residence_exceptions = dd.ds.LookupSet()

    residence_exceptions.add_items_from_file(
        file_path=os.path.join(data_path, "residence_exceptions.txt")
    )

    residences = dd.ds.LookupSet()

    residences.add_items_from_file(
        file_path=os.path.join(data_path, "residences.txt"),
        cleaning_pipeline=[
            dd.str.StripString(),
        ],
    )

    residences.add_items_from_file(
        file_path=os.path.join(data_path, "provinces.txt"),
        cleaning_pipeline=[
            dd.str.StripString(),
        ],
    )

    residences.add_items_from_file(
        file_path=os.path.join(data_path, "regions.txt"),
        cleaning_pipeline=[
            dd.str.StripString(),
        ],
    )

    residences.add_items_from_file(
        file_path=os.path.join(data_path, "municipalities.txt"),
        cleaning_pipeline=[
            dd.str.StripString(),
        ],
    )

    residences.remove_items_from_iterable(residence_exceptions)

    residences.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceNonAsciiCharacters()]
    )

    residences.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceValue("Sint", "St.")]
    )
    residences.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceValue("Sint", "st.")]
    )
    residences.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceValue("'t", "Het")])
    residences.add_items_from_self(cleaning_pipeline=[dd.str.ReplaceValue("'t", "het")])

    residences.add_items_from_self(
        cleaning_pipeline=[
            dd.str.ReplaceValue("-", " "),
            dd.str.ReplaceValue("  ", " "),
        ]
    )

    residences.add_items_from_self(
        cleaning_pipeline=[
            dd.str.ReplaceValue("(", ""),
            dd.str.ReplaceValue(")", ""),
            dd.str.ReplaceValue("  ", " "),
        ]
    )

    residences.add_items_from_self(cleaning_pipeline=[UpperCase()])

    residences.add_items_from_self(
        cleaning_pipeline=[
            FilterBasedOnLookupSet(filter_set=_get_whitelist(), case_sensitive=False),
        ],
        replace=True,
    )

    return residences


def _get_institutions() -> dd.ds.LookupSet:
    """Get institutions LookupSet."""

    institutions_raw = dd.ds.LookupSet()
    institutions_raw.add_items_from_file(
        os.path.join(data_path, "institutions.txt"),
        cleaning_pipeline=[dd.str.FilterByLength(min_len=3), dd.str.LowercaseString()],
    )

    institutions = dd.ds.LookupSet(matching_pipeline=[dd.str.LowercaseString()])
    institutions.add_items_from_iterable(
        institutions_raw, cleaning_pipeline=[dd.str.StripString()]
    )

    institutions.add_items_from_iterable(
        institutions_raw,
        cleaning_pipeline=[
            RemoveValues(
                filter_values=["dr.", "der", "van", "de", "het", "'t", "in", "d'"]
            ),
            dd.str.StripString(),
        ],
    )

    institutions.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceValue(".", ""), dd.str.StripString()]
    )

    institutions.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceValue("st ", "sint ")]
    )

    institutions.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceValue("st. ", "sint ")]
    )

    institutions.add_items_from_self(
        cleaning_pipeline=[dd.str.ReplaceValue("ziekenhuis", "zkh")]
    )

    institutions.add_items_from_self(
        cleaning_pipeline=[
            dd.str.LowercaseString(),
            Acronimify(),
            dd.str.FilterByLength(min_len=3),
        ]
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
        os.path.join(data_path, "surnames.txt"),
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
        "residences": _get_residences,
        "institutions": _get_institutions,
        "whitelist": _get_whitelist,
    }

    for name, init_function in lookup_set_mapping.items():
        lookup_sets[name] = init_function()

    return lookup_sets
