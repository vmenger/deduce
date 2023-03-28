import docdeid as dd

from deduce.lookup_sets import get_lookup_sets
from deduce.pattern.name_context import (
    InitialNameContextPattern,
    InitialsContextPattern,
    InterfixContextPattern,
    NexusContextPattern,
)
from tests.helpers import linked_tokens

lookup_sets = get_lookup_sets()


class TestInterfixContextPattern:
    pattern = InterfixContextPattern(lookup_sets=lookup_sets, tag="_")

    def test_match(self):
        tokens = linked_tokens(["Peter", "van der", "Vorst"])
        annotation = dd.Annotation(
            text="Peter", start_char=0, end_char=5, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) == (tokens[0], tokens[2])

    def test_match_wrong_tag(self):
        tokens = linked_tokens(["Peter", "van der", "Vorst"])
        annotation = dd.Annotation(
            text="Peter", start_char=0, end_char=5, tag="familielid", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) is None

    def test_match_not_capitalized(self):
        tokens = linked_tokens(["Peter", "van der", "vorst"])
        annotation = dd.Annotation(
            text="Peter", start_char=0, end_char=5, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) is None


class TestInitialsContextPattern:
    pattern = InitialsContextPattern(lookup_sets, tag="_")

    def test_match_initial(self):
        tokens = linked_tokens(["A", "J", "Hoekstra"])
        annotation = dd.Annotation(
            text="J Hoekstra",
            start_char=0,
            end_char=10,
            tag="initiaal+achternaam",
            start_token=tokens[1],
            end_token=tokens[2],
        )

        assert self.pattern.match(annotation) == (tokens[0], tokens[2])

    def test_match_naam(self):
        tokens = linked_tokens(["Albert", "Jan", "Hoekstra"])
        annotation = dd.Annotation(
            text="J Hoekstra",
            start_char=0,
            end_char=10,
            tag="voornaam+achternaam",
            start_token=tokens[1],
            end_token=tokens[2],
        )

        assert self.pattern.match(annotation) == (tokens[0], tokens[2])

    def test_unmatch_prefix(self):
        tokens = linked_tokens(["dhr", "J", "Hoekstra"])
        annotation = dd.Annotation(
            text="J Hoekstra",
            start_char=0,
            end_char=10,
            tag="initiaal+achternaam",
            start_token=tokens[1],
            end_token=tokens[2],
        )

        assert self.pattern.match(annotation) is None


class TestInitialNameContextPattern:
    pattern = InitialNameContextPattern(lookup_sets=lookup_sets, tag="_")

    def test_match_initial(self):
        tokens = linked_tokens(["M", "Oudshoorn"])
        annotation = dd.Annotation(
            text="M", start_char=0, end_char=1, tag="initiaal", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) == (tokens[0], tokens[1])

    def test_match_first_name(self):
        tokens = linked_tokens(["Mieke", "Oudshoorn"])
        annotation = dd.Annotation(
            text="Mieke", start_char=0, end_char=5, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) == (tokens[0], tokens[1])

    def test_match_prefix(self):
        tokens = linked_tokens(["mw", "Oudshoorn"])
        annotation = dd.Annotation(
            text="mw", start_char=0, end_char=2, tag="prefix", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) == (tokens[0], tokens[1])

    def test_short_surname(self):
        tokens = linked_tokens(["mw", "Li"])
        annotation = dd.Annotation(
            text="mw", start_char=0, end_char=2, tag="prefix", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) is None


class TestNexusContextPattern:
    pattern = NexusContextPattern(tag="_")

    def test_match(self):
        tokens = linked_tokens(["Laura", "en", "Mieke"])
        annotation = dd.Annotation(
            text="Laura", start_char=0, end_char=5, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) == (tokens[0], tokens[2])

    def test_no_match_lowercase(self):
        tokens = linked_tokens(["Laura", "en", "zoon"])
        annotation = dd.Annotation(
            text="Laura", start_char=0, end_char=5, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
        )

        assert self.pattern.match(annotation) is None
