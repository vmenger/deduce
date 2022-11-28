from deduce.utils import any_in_text, str_match


class TestUtils:
    def test_any_in_text(self):

        assert any_in_text(["hans", "piet", "karel"], "ik heet hans")
        assert any_in_text(["hans", "piet", "karel"], "ik heet piet")
        assert any_in_text(["hans", "piet", "karel"], "ik heet karel")
        assert any_in_text(["hans", "piet", "karel"], "wij heten hans, piet en karel")
        assert not any_in_text(["hans", "piet", "karel"], "ik heet peter")
        assert any_in_text(["hans", "piet", "karel"], "wat een leuk hansopje")
        assert any_in_text(["hans", "piet", "karel"], "mijn oom heet pieter")

    def test_str_match(self):

        assert str_match("a", "a")
        assert str_match("willem", "willem")
        assert not str_match("a", "b")
        assert not str_match("willem", "klaas")

    def test_str_match_fuzzy(self):

        assert str_match("a", "a", max_edit_distance=1)
        assert str_match("willem", "willem", max_edit_distance=1)
        assert str_match("willem", "illem", max_edit_distance=1)
        assert str_match("willem", "qwillem", max_edit_distance=1)
        assert str_match("willem", "willme", max_edit_distance=1)
        assert str_match("willem", "Willem", max_edit_distance=1)

        assert not str_match("a", "abc", max_edit_distance=1)
        assert not str_match("willem", "wilhelm", max_edit_distance=1)
        assert not str_match("willem", "klaas", max_edit_distance=1)
