from pathlib import Path

import docdeid as dd
import pytest

from deduce import utils
from deduce.annotator import TokenPatternAnnotator


class TestStrMatch:
    def test_str_match(self):
        assert utils.str_match("a", "a")
        assert utils.str_match("willem", "willem")
        assert not utils.str_match("a", "b")
        assert not utils.str_match("willem", "klaas")

    def test_str_match_fuzzy(self):
        assert utils.str_match("a", "a", max_edit_distance=1)
        assert utils.str_match("willem", "willem", max_edit_distance=1)
        assert utils.str_match("willem", "illem", max_edit_distance=1)
        assert utils.str_match("willem", "qwillem", max_edit_distance=1)
        assert utils.str_match("willem", "willme", max_edit_distance=1)
        assert utils.str_match("willem", "Willem", max_edit_distance=1)

        assert not utils.str_match("a", "abc", max_edit_distance=1)
        assert not utils.str_match("willem", "wilhelm", max_edit_distance=1)
        assert not utils.str_match("willem", "klaas", max_edit_distance=1)


class TestClassFromName:
    def test_class_from_name(self):
        assert (
            utils.get_class_from_name(
                module_name="deduce.annotator", class_name="TokenPatternAnnotator"
            )
            == TokenPatternAnnotator
        )


class TestInitializeClass:
    def test_initialize_class(self):
        cls = TokenPatternAnnotator

        tag = "_"
        pattern = [{"key": "value"}]

        annotator = utils.initialize_class(
            cls, args={"tag": tag, "pattern": pattern}, extras={}
        )

        assert annotator.tag == tag
        assert annotator.pattern == pattern

    def test_initialize_class_with_extras(self):
        cls = TokenPatternAnnotator

        tag = "_"
        pattern = [{"key": "value"}]
        ds = dd.ds.DsCollection()

        annotator = utils.initialize_class(
            cls,
            args={"tag": tag, "pattern": pattern},
            extras={"ds": ds, "unused_argument": "_"},
        )

        assert annotator.tag == tag
        assert annotator.pattern == pattern
        assert annotator.ds is ds


class TestOverwriteDict:
    def test_empty(self):
        for add in [{}, {"a": 1}, {"a": 1, "b": {}}, {"a": 1, "b": {"c": 2}}]:
            assert utils.overwrite_dict({}, add) == add

    def test_nonempty_no_nesting(self):
        assert utils.overwrite_dict({"a": 1}, {"a": 1}) == {"a": 1}
        assert utils.overwrite_dict({"a": 1}, {"a": 2}) == {"a": 2}
        assert utils.overwrite_dict({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_nonempty_with_nesting(self):
        assert utils.overwrite_dict({"a": 1, "b": {"c": 2}}, {"b": {"c": 4}}) == {
            "a": 1,
            "b": {"c": 4},
        }
        assert utils.overwrite_dict({"a": 1, "b": {"c": 2}}, {"b": {"d": 4}}) == {
            "a": 1,
            "b": {"c": 2, "d": 4},
        }


class TestHasOverlap:
    def test_has_overlap(self):
        assert not utils.has_overlap([])
        assert not utils.has_overlap([(0, 10)])
        assert utils.has_overlap([(0, 10), (5, 15)])
        assert not utils.has_overlap([(0, 10), (10, 15)])
        assert not utils.has_overlap([(0, 10), (15, 25)])
        assert not utils.has_overlap([(15, 25), (0, 10)])


class TestStrVariations:
    def test_has_overlap(self):
        assert utils.has_overlap([(0, 10), (5, 14)])
        assert utils.has_overlap([(0, 10), (9, 15)])
        assert utils.has_overlap([(9, 15), (5, 10)])
        assert utils.has_overlap([(9, 15, True), (5, 10, False)])
        assert not utils.has_overlap([(0, 10), (10, 13)])
        assert not utils.has_overlap([(0, 10), (10, 10)])
        assert not utils.has_overlap([(0, 10, True), (10, 10, False)])

    def test_repl_none(self):
        s = "Prof. Lieflantlaan"
        matches = []

        segments = utils.repl_segments(s, matches)

        assert segments == [["Prof. Lieflantlaan"]]

    def test_repl_segments_single_to_single(self):
        s = "Prof. Lieflantlaan"
        matches = [(0, 5, ["Prof."])]

        segments = utils.repl_segments(s, matches)

        assert segments == [["Prof."], [" Lieflantlaan"]]

    def test_repl_segments_single_to_multiple(self):
        s = "Prof. Lieflantlaan"
        matches = [(0, 5, ["Prof.", "Professor"])]

        segments = utils.repl_segments(s, matches)

        assert segments == [["Prof.", "Professor"], [" Lieflantlaan"]]

    def test_repl_segments_multiple_to_multiple(self):
        s = "Prof. Lieflantlaan"
        matches = [(0, 5, ["Prof.", "Professor"]), (14, 18, ["laan", "ln"])]

        segments = utils.repl_segments(s, matches)

        assert segments == [["Prof.", "Professor"], [" Lieflant"], ["laan", "ln"]]

    def test_str_variations_no_matches(self):
        s = "Prof. Lieflantlaan"
        repl = {}

        variations = utils.str_variations(s, repl)

        assert variations == [s]

    def test_str_variations_overlap(self):
        s = "Prof. Lieflantlaan"
        repl = {"laan": ["laan", "ln"], "lantlaan": ["lantlaan", "lantln"]}

        with pytest.raises(RuntimeError):
            _ = utils.str_variations(s, repl)

    def test_str_variations_one_match(self):
        s = "Prof. Lieflantlaan"
        repl = {"Prof.": ["Prof.", "Professor"]}

        variations = utils.str_variations(s, repl)

        assert variations == ["Prof. Lieflantlaan", "Professor Lieflantlaan"]

    def test_str_variations_multiple_matches(self):
        s = "Prof. Lieflantlaan"
        repl = {"Prof.": ["Prof.", "Professor"], "laan": ["laan", "ln"]}

        variations = utils.str_variations(s, repl)

        assert variations == [
            "Prof. Lieflantlaan",
            "Professor Lieflantlaan",
            "Prof. Lieflantln",
            "Professor Lieflantln",
        ]

    def test_str_variations_regexp(self):
        s = "van Bevanstraat"
        repl = {"^van": ["Van", "van"]}

        variations = utils.str_variations(s, repl)

        assert variations == ["Van Bevanstraat", "van Bevanstraat"]

    def test_apply_transform(self):
        s = {"Prof. Lieflantlaan"}
        repl = {"Prof.": ["Prof.", "Professor"]}

        transform_config = {"transforms": {"prefix": repl}}
        variations = utils.apply_transform(s, transform_config)

        assert variations == {"Prof. Lieflantlaan", "Professor Lieflantlaan"}

    def test_apply_transform2(self):
        items = {"den Burg", "Rotterdam"}
        transform = {"transforms": {"name": {"den": ["den", ""]}}}

        transformed_items = utils.apply_transform(items, transform)

        assert transformed_items == {"den Burg", "Burg", "Rotterdam"}

    def test_apply_transform_no_strip_lines(self):
        items = {"den Burg", "Rotterdam"}
        transform = {"transforms": {"name": {"den": ["den", ""]}}, "strip_lines": False}

        transformed_items = utils.apply_transform(items, transform)

        assert transformed_items == {"den Burg", " Burg", "Rotterdam"}


class TestOptionalLoad:
    def test_optional_load_items(self):
        path = Path("tests/data/lookup/src/lst_test_nested/items.txt")

        assert utils.optional_load_items(path) == {"a", "b"}

    def test_optional_load_items_nonexisting(self):
        path = Path("tests/data/non/existing/file.txt")

        assert utils.optional_load_items(path) is None

    def test_optional_load_json(self):
        path = Path("tests/data/small.json")

        assert utils.optional_load_json(path) == {"test": True}

    def test_optional_load_json_nonexisting(self):
        path = Path("tests/data/non/existing/file.json")

        assert utils.optional_load_json(path) is None
