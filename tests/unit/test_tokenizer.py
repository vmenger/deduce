import docdeid as dd
import pytest

from deduce.tokenizer import DeduceTokenizer


@pytest.fixture
def tokens():
    return [
        dd.Token(text="Patient", start_char=0, end_char=7),
        dd.Token(text="was", start_char=8, end_char=11),
        dd.Token(text="eerder", start_char=12, end_char=18),
        dd.Token(text="opgenomen", start_char=19, end_char=28),
        dd.Token(text="(", start_char=29, end_char=30),
        dd.Token(text="vorig", start_char=30, end_char=35),
        dd.Token(text="jaar", start_char=36, end_char=40),
        dd.Token(text=")", start_char=40, end_char=41),
        dd.Token(text="alhier", start_char=42, end_char=48),
        dd.Token(text=".", start_char=48, end_char=49),
    ]


class TestTokenizer:
    def test_split_alpha(self):
        tokenizer = DeduceTokenizer()
        text = "Pieter van der Zee"
        expected_tokens = [
            dd.Token(text="Pieter", start_char=0, end_char=6),
            dd.Token(text="van", start_char=7, end_char=10),
            dd.Token(text="der", start_char=11, end_char=14),
            dd.Token(text="Zee", start_char=15, end_char=18),
        ]

        assert tokenizer._split_text(text=text) == expected_tokens

    def test_split_nonalpha(self):
        tokenizer = DeduceTokenizer()
        text = "prematuur (<p3)"

        expected_tokens = [
            dd.Token(text="prematuur", start_char=0, end_char=9),
            dd.Token(text="(", start_char=10, end_char=11),
            dd.Token(text="<", start_char=11, end_char=12),
            dd.Token(text="p3", start_char=12, end_char=14),
            dd.Token(text=")", start_char=14, end_char=15),
        ]

        assert tokenizer._split_text(text=text) == expected_tokens

    def test_split_newline(self):
        tokenizer = DeduceTokenizer()
        text = "regel 1 \n gevolgd door regel 2"

        expected_tokens = [
            dd.Token(text="regel", start_char=0, end_char=5),
            dd.Token(text="1", start_char=6, end_char=7),
            dd.Token(text="\n", start_char=8, end_char=9),
            dd.Token(text="gevolgd", start_char=10, end_char=17),
            dd.Token(text="door", start_char=18, end_char=22),
            dd.Token(text="regel", start_char=23, end_char=28),
            dd.Token(text="2", start_char=29, end_char=30),
        ]

        assert tokenizer._split_text(text=text) == expected_tokens

    def test_join_tokens(self, tokens):
        text = "Patient was eerder opgenomen"
        joined_token = DeduceTokenizer()._join_tokens(text, tokens[0:4])
        expected_token = dd.Token(text=text, start_char=0, end_char=28)

        assert joined_token == expected_token

    def test_split_with_merge(self):
        tokenizer = DeduceTokenizer(merge_terms=["van der"])
        text = "Pieter van der Zee"
        expected_tokens = [
            dd.Token(text="Pieter", start_char=0, end_char=6),
            dd.Token(text="van der", start_char=7, end_char=14),
            dd.Token(text="Zee", start_char=15, end_char=18),
        ]

        assert tokenizer._split_text(text=text) == expected_tokens
