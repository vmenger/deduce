from unittest.mock import patch

import docdeid as dd

from deduce.pattern.name_patient import (
    PersonFirstNamePattern,
    PersonInitialFromNamePattern,
    PersonInitialsPattern,
    PersonSurnamePattern,
)
from deduce.person import Person
from deduce.tokenizer import DeduceTokenizer
from tests.helpers import linked_tokens


class TestPersonFirstNamePattern:
    pattern = PersonFirstNamePattern(tag="_")

    def test_match_first_name_multiple(self):
        metadata = {"patient": Person(first_names=["Jan", "Adriaan"])}
        tokens = linked_tokens(["Jan", "Adriaan"])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[0],
        )
        assert self.pattern.match(tokens[1], metadata=metadata) == (
            tokens[1],
            tokens[1],
        )

    def test_match_first_name_fuzzy(self):
        metadata = {"patient": Person(first_names=["Adriaan"])}
        tokens = linked_tokens(["Adriana"])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[0],
        )

    def test_match_first_name_fuzzy_short(self):
        metadata = {"patient": Person(first_names=["Jan"])}
        tokens = linked_tokens(["Dan"])

        assert self.pattern.match(tokens[0], metadata=metadata) is None


class TestPersonInitialFromNamePattern:
    pattern = PersonInitialFromNamePattern(tag="_")

    def test_match(self):
        metadata = {"patient": Person(first_names=["Jan", "Adriaan"])}

        tokens = linked_tokens(["A", "J"])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[0],
        )
        assert self.pattern.match(tokens[1], metadata=metadata) == (
            tokens[1],
            tokens[1],
        )

    def test_match_with_period(self):
        metadata = {"patient": Person(first_names=["Jan", "Adriaan"])}
        tokens = linked_tokens(["J", ".", "A", "."])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[1],
        )
        assert self.pattern.match(tokens[2], metadata=metadata) == (
            tokens[2],
            tokens[3],
        )

    def test_no_match(self):
        metadata = {"patient": Person(first_names=["Jan", "Adriaan"])}
        tokens = linked_tokens(["F", "T"])

        assert self.pattern.match(tokens[0], metadata=metadata) is None
        assert self.pattern.match(tokens[1], metadata=metadata) is None


class TestPersonInitialsPattern:
    pattern = PersonInitialsPattern(tag="_")

    def test_match(self):
        metadata = {"patient": Person(initials="AFTH")}
        tokens = linked_tokens(["AFTH", "THFA"])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[0],
        )
        assert self.pattern.match(tokens[1], metadata=metadata) is None


class TestPersonSurnamePattern:
    surname = "Van der Heide-Ginkel"
    surname_pattern = linked_tokens(["Van der", "Heide", "-", "Ginkel"])

    tokenizer = DeduceTokenizer()
    patch.object(tokenizer, "tokenize", return_value=surname_pattern).start()

    pattern = PersonSurnamePattern(tokenizer=tokenizer, tag="_")

    def test_doc_precondition(self):
        metadata = {"patient": Person(surname=self.surname)}
        doc = dd.Document(text="_", metadata=metadata)
        self.pattern.doc_precondition(doc)

        assert metadata["surname_pattern"] == self.surname_pattern

    def test_match_equal(self):
        metadata = {"surname_pattern": self.surname_pattern}
        tokens = linked_tokens(["Van der", "Heide", "-", "Ginkel", "is", "de", "naam"])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[3],
        )

    def test_match_longer_than_tokens(self):
        metadata = {"surname_pattern": self.surname_pattern}
        tokens = linked_tokens(["Van der", "Heide"])

        assert self.pattern.match(tokens[0], metadata=metadata) is None

    def test_match_fuzzy(self):
        metadata = {"surname_pattern": self.surname_pattern}
        tokens = linked_tokens(["Van der", "Heijde", "-", "Ginkle", "is", "de", "naam"])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[3],
        )

    def test_match_unequal_first(self):
        metadata = {"surname_pattern": self.surname_pattern}
        tokens = linked_tokens(["v/der", "Heide", "-", "Ginkel", "is", "de", "naam"])

        assert self.pattern.match(tokens[0], metadata=metadata) is None

    def test_match_unequal_first_fuzzy(self):
        metadata = {"surname_pattern": self.surname_pattern}
        tokens = linked_tokens(["Van den", "Heide", "-", "Ginkel", "is", "de", "naam"])

        assert self.pattern.match(tokens[0], metadata=metadata) == (
            tokens[0],
            tokens[3],
        )
