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
        result = annotate.annotate_names_context("Peter Parker")
        self.assertTrue(isinstance(result, str))


if __name__ == "__main__":
    unittest.main()
