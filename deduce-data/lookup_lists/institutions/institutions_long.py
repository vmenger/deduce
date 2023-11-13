"""
Creates streets_long.txt from streets_manual.txt by applying combinations of
replacements.

As a separate script to improve startup time, needs to be rerun when changes in this
script or in any of the street source lists are made.
"""

from deduce.utils import str_variations

zkh_mapping = {
    r" Ziekenhuis": [" Ziekenhuis", " Ziekenhuizen", " Zkh", " Zkh.", " Gasthuis",
                      " ziekenhuis", " ziekenhuizen", " gasthuis", " zkh", " zkh.",
                      "ziekenhuis", "ziekenhuizen", "gasthuis", "zkh", "zkh."],
    r"^Ziekenhuis": ["Ziekenhuis", "Zkh", "Zkh.", "Gasthuis", "ziekenhuis", "zkh", "zkh.", "gasthuis"],
    r"Medisch Centrum": ["Medisch Centrum", "MC"],
}

# Gasthuis -> gasthuis
# kliniek -> kliniek
# ziekenhuizen, ziekenhuisgroep?

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

    with open("ziekenhuizen.txt", "r") as file:
        institutions = set(file.read().split("\n"))

    for mapping in mappings:

        to_add = []

        for institution in institutions:
            to_add += str_variations(institution, mapping)

        institutions.update(to_add)

    placenames = {s.strip() for s in institutions}

    with open("institutions_long.txt", "w") as file:
        file.write("\n".join(sorted(list(placenames))))
