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
    province_mapping,
    punct_mapping,
    spell_mapping,
]


if __name__ == "__main__":

    with open("residences_raw.txt", "r") as file:
        residences = set(file.read().split("\n"))

    with open("residence_exceptions.txt", "r") as file:
        residences_exceptions = set(file.read().split("\n"))

    residences.difference_update(residences_exceptions)

    for mapping in mappings:

        to_add = []

        for residence in residences:
            to_add += str_variations(residence, mapping)

        residences.update(to_add)

    residences = {s.strip() for s in residences}

    with open("residences_long.txt", "w") as file:
        file.write("\n".join(sorted(list(residences))))
