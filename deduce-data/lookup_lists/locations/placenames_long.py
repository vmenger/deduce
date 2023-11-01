"""
Creates streets_long.txt from streets_manual.txt by applying combinations of
replacements.

As a separate script to improve startup time, needs to be rerun when changes in this
script or in any of the street source lists are made.
"""

from deduce.utils import str_variations

prefix_mapping = {
    r"\bhet\b": ["Het", "het", "'T", "'t", "`T", "`t", "T", "t"],
    r"\bSint\b": ["Sint", "sint", "St.", "st."],
    r"\bit\b": ["It", "it", "Het", "het", "'T", "'t", "`T", "`t", "T", "t"],
}


prop_mapping = {
    r"(\b|^)Aan\b": ["Aan", "aan"],
    r"(\b|^)Bij\b": ["Bij", "bij"],
    r"(\b|^)De\b": ["De", "de"],
    r"(\b|^)Den\b": ["Den", "den"],
    r"(\b|^)En\b": ["En", "en"],
    r"(\b|^)Het\b": ["Het", "het", "'T", "'t", "`T", "`t", "T", "t"],
    r"(\b|^)In\b": ["In", "in"],
    r"(\b|^)Oan\b": ["Oan", "oan"],
    r"(\b|^)Of\b": ["Of", "of"],
    r"(\b|^)Op\b": ["Op", "op"],
    r"(\b|^)Over\b": ["Over", "over"],
    r"(\b|^)'S\b": ["'S", "'s"],
    r"(\b|^)Ter\b": ["Ter", "ter"],
    r"(\b|^)Van\b": ["Van", "van", "v.", "V."],
}

province_mapping = {
    r"(?<=\()Fr(?=\))": ["Fr", "FR", "Frl", "FRL", "F"],
    r"(?<=\()Gr(?=\))": ["Gr", "GR", "Gn", "GN", "G"],
    r"(?<=\()Dr(?=\))": ["Dr", "DR", "Dn", "DN", "D"],
    r"(?<=\()Ov(?=\))": ["Ov", "OV", "O"],
    r"(?<=\()Nh(?=\))": ["Nh", "NH"],
    r"(?<=\()Ut(?=\))": ["Ut", "UT", "U"],
    r"(?<=\()Gld(?=\))": ["Gld", "GLD", "G"],
    r"(?<=\()Li(?=\))": ["Li", "LI", "L"],
    r"(?<=\()Nb(?=\))": ["Nb", "NB"],
    r"(?<=\()Zh(?=\))": ["Zh", "ZH"],
    r"(?<=\()Ze(?=\))": ["Ze", "ZE", "Z"],
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
    prefix_mapping,
    prop_mapping,
    province_mapping,
    punct_mapping,
    spell_mapping,
]


if __name__ == "__main__":

    with open("residences.txt", "r") as file:
        residences = set(file.read().split("\n"))

    with open("residence_exceptions.txt", "r") as file:
        residence_exceptions = set(file.read().split("\n"))

    residences.difference_update(residence_exceptions)

    with open("regions.txt", "r") as file:
        regions = set(file.read().split("\n"))

    with open("provinces.txt", "r") as file:
        provinces = set(file.read().split("\n"))

    with open("municipalities.txt", "r") as file:
        municipalities = set(file.read().split("\n"))

    placenames = set()
    placenames.update(regions)
    placenames.update(provinces)
    placenames.update(municipalities)
    placenames.update(residences)

    for mapping in mappings:

        to_add = []

        for placename in placenames:
            to_add += str_variations(placename, mapping)

        placenames.update(to_add)

    placenames = {s.strip() for s in placenames}

    with open("placenames_long.txt", "w") as file:
        file.write("\n".join(sorted(list(placenames))))
