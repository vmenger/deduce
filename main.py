from deduce.deduce import deduce_model
from deduce.deduce import annotate_text, deidentify_annotations

from docdeid.annotation.annotation_processor import LongestFirstOverlapResolver

from deduce.annotate import *

def main1():


    text = "Pieter en Maria"

    doc = deduce_model.deidentify(text=text, meta_data={})

    print("===")

    print(doc.text)
    print(doc.annotations)
    print(doc.deidentified_text)

    print("===")

    annotated = annotate_text(text=text)
    deidentified = deidentify_annotations(annotated)

    print(annotated)
    print(deidentified)

def main2():

    text = "ik kreeg een e-mail van Hans via het emailadres Ter Apel@gmail.com"

    doc = deduce_model.deidentify(text=text, meta_data={'patient_first_names': 'Hans', 'patient_surname': 'Bakker'})
    print("")
    print(doc.annotations)

    overlap = LongestFirstOverlapResolver()
    print(overlap.process(doc.annotations))



if __name__ == '__main__':
    main1()