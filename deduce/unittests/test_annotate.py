import unittest
from unittest.mock import patch

from deduce import utility, annotate

from deduce.annotate import annotate_names
from deduce.utilcls import Annotation


class TestAnnotateMethods(unittest.TestCase):
    def test_annotate_names(self):
        annotations = annotate_names("Peter  Parker", "Peter", "P.", "Parker", "Pete")
        expected_annotations = [Annotation(0, 5, "VOORNAAMPAT", "Peter"),
                                Annotation(7, 13, "ACHTERNAAMPAT", "Parker")]
        self.assertEqual(2, len(expected_annotations))
        self.assertEqual(expected_annotations, annotations)

    def test_annotate_names_context(self):
        result = annotate.annotate_names_context("Peter Parker", [])
        self.assertEqual(list, type(result))

    def test_insert_annotations(self):
        text = "Jan Jansen en Pieter van Duinen kwamen"
        annotations = [Annotation(0, 10, "PERSOON", "Jan Jansen"),
                       Annotation(14, 31, "PATIENT", "Pieter van Duinen")]
        expected_text = "<PERSOON Jan Jansen> en <PATIENT Pieter van Duinen> kwamen"
        retrieved_text = annotate.insert_annotations(text, annotations)
        self.assertEqual(expected_text, retrieved_text)

    def test_remove_annotations_in_range(self):
        annotations = [Annotation(0, 10, "PERSOON", "Jan Jansen"),
                       Annotation(14, 31, "PATIENT", "Pieter van Duinen")]
        retrieved_annotations = annotate.remove_annotations_in_range(annotations, 14, 31)
        self.assertEqual([annotations[0]], retrieved_annotations)

if __name__ == "__main__":
    unittest.main()
