import docdeid as dd
import pytest

from deduce.tokenize import DeduceTokenizer


@pytest.fixture
def tokens():
    return [
        dd.Token(text="Patient", start_char=0, end_char=7),
        dd.Token(text=" ", start_char=7, end_char=8),
        dd.Token(text="was", start_char=8, end_char=11),
        dd.Token(text=" ", start_char=11, end_char=12),
        dd.Token(text="eerder", start_char=12, end_char=18),
        dd.Token(text=" ", start_char=18, end_char=19),
        dd.Token(text="opgenomen", start_char=19, end_char=28),
        dd.Token(text=" ", start_char=28, end_char=29),
        dd.Token(text="(", start_char=29, end_char=30),
        dd.Token(text="vorig", start_char=30, end_char=35),
        dd.Token(text=" ", start_char=35, end_char=36),
        dd.Token(text="jaar", start_char=36, end_char=40),
        dd.Token(text=")", start_char=40, end_char=41),
        dd.Token(text=" ", start_char=41, end_char=42),
        dd.Token(text="alhier", start_char=42, end_char=48),
        dd.Token(text=".", start_char=48, end_char=49),
    ]


class TestTokenizer:
    def test_split_text_no_merge(self):

        tokenizer = DeduceTokenizer()
        text = "Pieter van der Zee"
        expected_tokens = [
            dd.Token(text="Pieter", start_char=0, end_char=6),
            dd.Token(text=" ", start_char=6, end_char=7),
            dd.Token(text="van", start_char=7, end_char=10),
            dd.Token(text=" ", start_char=10, end_char=11),
            dd.Token(text="der", start_char=11, end_char=14),
            dd.Token(text=" ", start_char=14, end_char=15),
            dd.Token(text="Zee", start_char=15, end_char=18),
        ]

        assert tokenizer._split_text(text=text) == expected_tokens

    def test_split_with_merge(self):

        tokenizer = DeduceTokenizer(merge_terms=["van der"])
        text = "Pieter van der Zee"
        expected_tokens = [
            dd.Token(text="Pieter", start_char=0, end_char=6),
            dd.Token(text=" ", start_char=6, end_char=7),
            dd.Token(text="van der", start_char=7, end_char=14),
            dd.Token(text=" ", start_char=14, end_char=15),
            dd.Token(text="Zee", start_char=15, end_char=18),
        ]

        assert tokenizer._split_text(text=text) == expected_tokens

    def test_next_token(self, tokens):

        tokenizer = DeduceTokenizer()

        assert tokenizer._next_token(0, tokens) is tokens[2]
        assert tokenizer._next_token(6, tokens) is tokens[9]
        assert tokenizer._next_token(7, tokens) is tokens[9]
        assert tokenizer._next_token(8, tokens) is tokens[9]
        assert tokenizer._next_token(11, tokens) is None
        assert tokenizer._next_token(14, tokens) is None
        assert tokenizer._next_token(15, tokens) is None

    def test_previous_token(self, tokens):

        tokenizer = DeduceTokenizer()
        assert tokenizer._previous_token(0, tokens) is None
        assert tokenizer._previous_token(1, tokens) == tokens[0]
        assert tokenizer._previous_token(2, tokens) == tokens[0]
        assert tokenizer._previous_token(7, tokens) == tokens[6]
        assert tokenizer._previous_token(9, tokens) is None
        assert tokenizer._previous_token(10, tokens) is tokens[9]

    def test_join_tokens(self, tokens):

        joined_token = DeduceTokenizer()._join_tokens(tokens[0:7])
        expected_token = dd.Token(text="Patient was eerder opgenomen", start_char=0, end_char=28)

        assert joined_token == expected_token
