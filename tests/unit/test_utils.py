import pytest

from deduce import utils


class TestUtils:
    def test_any_in_text(self):
        assert utils.any_in_text(["hans", "piet", "karel"], "ik heet hans")
        assert utils.any_in_text(["hans", "piet", "karel"], "ik heet piet")
        assert utils.any_in_text(["hans", "piet", "karel"], "ik heet karel")
        assert utils.any_in_text(
            ["hans", "piet", "karel"], "wij heten hans, piet en karel"
        )
        assert not utils.any_in_text(["hans", "piet", "karel"], "ik heet peter")
        assert utils.any_in_text(["hans", "piet", "karel"], "wat een leuk hansopje")
        assert utils.any_in_text(["hans", "piet", "karel"], "mijn oom heet pieter")

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
