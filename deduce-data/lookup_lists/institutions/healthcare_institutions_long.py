"""
Creates streets_long.txt from streets_manual.txt by applying combinations of
replacements.

As a separate script to improve startup time, needs to be rerun when changes in this
script or in any of the street source lists are made.
"""

from deduce.utils import str_variations

inst_mapping = {
    "Huisartsenpraktijk": [
        "Huisartsenpraktijk",
        "huisartsenpraktijk",
        "Huisartspraktijk",
        "huisartspraktijk",
    ]
}

prefix_mapping = {r"\bDe\b": ["De", "de"]}

punct_mapping = {r"\.": [".", ""], r"-": ["-", "", " "], r" & ": [" & ", " en "]}

spell_mapping = {
    "y": ["y", "ij"],
    "Y": ["Y", "IJ"],
    "ij": ["ij", "y"],
    "IJ": ["IJ", "Y"],
}

mappings = [
    inst_mapping,
    prefix_mapping,
    punct_mapping,
    spell_mapping,
]


if __name__ == "__main__":

    with open("healthcare_institutions.txt", "r") as file:
        institutions = set(file.read().split("\n"))

    with open("healthcare_institution_exceptions.txt", "r") as file:
        exceptions = set(file.read().split("\n"))

    institutions = institutions - exceptions

    for mapping in mappings:

        to_add = []

        for institution in institutions:
            to_add += str_variations(institution, mapping)

        institutions.update(to_add)

    placenames = {s.strip() for s in institutions}

    with open("healthcare_institutions_long.txt", "w") as file:
        file.write("\n".join(sorted(list(placenames))))
