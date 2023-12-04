import json

"""
Creates streets_long.txt from streets_manual.txt by applying combinations of
replacements.

As a separate script to improve startup time, needs to be rerun when changes in this
script or in any of the street source lists are made.
"""

from deduce.utils import str_variations

if __name__ == "__main__":

    with open("items.txt", "r") as file:
        hospitals = set(file.read().split("\n"))

    with open("transform.json", 'r') as file:
        transformations = json.load(file)['transformations']
    for _, transform in transformations.items():

        to_add = []

        for hospital in hospitals:
            to_add += str_variations(hospital, transform)

        hospitals.update(to_add)

    placenames = {s.strip() for s in hospitals}

    with open("hospital_long.txt", "w") as file:
        file.write("\n".join(sorted(list(placenames))))
