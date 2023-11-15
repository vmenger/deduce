"""
Creates streets_long.txt from streets_manual.txt by applying combinations of
replacements.

As a separate script to improve startup time, needs to be rerun when changes in this
script or in any of the street source lists are made.
"""

from deduce.utils import str_variations

zkh_mapping = {
    r" (Ziekenhuis|Gasthuis|Kliniek)": [
        " Ziekenhuis",
        " Ziekenhuizen",
        " Zkh",
        " Zkh.",
        " Gasthuis",
        " Kliniek",
        " Klinieken",
        " ziekenhuis",
        " ziekenhuizen",
        " zkh",
        " zkh.",
        " gasthuis",
        " kliniek",
        " klinieken",
        "ziekenhuis",
        "ziekenhuizen",
        "zkh",
        "zkh.",
        "gasthuis",
        "kliniek",
        "klinieken",
    ],
    r"^(Ziekenhuis|Gasthuis|Kliniek)": [
        "Ziekenhuis",
        "Zkh",
        "Zkh.",
        "Gasthuis",
        "Kliniek",
        "ziekenhuis",
        "zkh",
        "zkh.",
        "gasthuis",
        "kliniek",
    ],
    r"Medisch Centrum": ["Medisch Centrum", "MC"],
}

zkh_mapping_2 = {
    r"Universitair Medisch Centrum": ["Universitair Medisch Centrum", "UMC"],
}

prefix_mapping = {
    r"\bhet\b": ["Het", "het", "'T", "'t", "`T", "`t", "T", "t", ""],
    r"\bSint\b": ["Sint", "sint", "St.", "st.", "st", ""],
}

punct_mapping = {
    r"\.": [".", ""],
    "-": ["-", "", " "],
}

spell_mapping = {
    "y": ["y", "ij"],
    "Y": ["Y", "IJ"],
    "ij": ["ij", "y"],
    "IJ": ["IJ", "Y"],
}

mappings = [
    zkh_mapping,
    zkh_mapping_2,
    prefix_mapping,
    punct_mapping,
    spell_mapping,
]


if __name__ == "__main__":

    with open("hospitals.txt", "r") as file:
        hospitals = set(file.read().split("\n"))

    for mapping in mappings:

        to_add = []

        for hospital in hospitals:
            to_add += str_variations(hospital, mapping)

        hospitals.update(to_add)

    placenames = {s.strip() for s in hospitals}

    with open("hospital_long.txt", "w") as file:
        file.write("\n".join(sorted(list(placenames))))
