from datetime import datetime

import pytest


class TestBoosterRecall:
    @pytest.mark.parametrize(
        "text, expected_texts",
        [
            ("on date 12 08 2012", ["12 08 2012"]),
            ("on date 12 januari 2012", ["12 januari 2012"]),
            ("on date 2012 12 08", ["2012 12 08"]),
            ("on date 2012 januari 5", ["2012 januari 5"]),
        ],
    )
    def test_overlap_resolve_year(self, model_with_recall_boost, text, expected_texts):
        """In the specific case of space separated dates that contain a
        year the year gets annotated again by the date_dmy_1 annotator.
        Due to length priority this extra annotation should be removed,
        which is tested here.
        """
        result = model_with_recall_boost.deidentify(text)
        resulting_texts = [ann.text for ann in result.annotations]
        assert resulting_texts == expected_texts

    def test_current_year_replace(self, model_with_recall_boost):
        """The maximum year is capped in the year only regex, just in case
        deduce will last a long time this test will fail if the year
        surpasses the maximum year that is defined currently -> 2029."""
        current_year = datetime.now().year
        text = f"on date 12 08 {current_year}"
        result = model_with_recall_boost.deidentify(text)
        resulting_texts = [ann.text for ann in result.annotations]
        assert resulting_texts == [text[-10:]]
