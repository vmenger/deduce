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
