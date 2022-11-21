import docdeid as dd
import pytest

from deduce.lookup_sets import get_lookup_sets
from deduce.pattern.name import (
    FirstNameLookupPattern,
    InitiaalInterfixCapitalPattern,
    InitialWithCapitalPattern,
    InterfixWithNamePattern,
    PrefixWithNamePattern,
    SurnameLookupPattern,
)
from tests.helpers import linked_tokens

lookup_sets = get_lookup_sets()


@pytest.fixture
def meta_data():
    return dd.MetaData()


class TestPrefixWithNamePattern:

    pattern = PrefixWithNamePattern(lookup_sets=lookup_sets, tag="_")

    def test_prefix_with_uppercase(self, meta_data):

        tokens = linked_tokens(["dhr", "Pieterse"])

        assert self.pattern.match(tokens[0], meta_data) == (tokens[0], tokens[1])

    def test_prefix_with_lowercase(self, meta_data):

        tokens = linked_tokens(["dhr", "pieterse"])

        assert self.pattern.match(tokens[0], meta_data) is None


class TestInterfixWithNamePattern:

    pattern = InterfixWithNamePattern(lookup_sets=lookup_sets, tag="_")

    def test_interfix(self, meta_data):

        tokens = linked_tokens(["van der", "Poel"])

        assert self.pattern.match(tokens[0], meta_data) == (tokens[0], tokens[1])

    def test_interfix_no_surname(self, meta_data):

        tokens = linked_tokens(["van der", "Hamstra"])

        assert self.pattern.match(tokens[0], meta_data) is None


class TestInitialWithCapitalPattern:

    pattern = InitialWithCapitalPattern(lookup_sets=lookup_sets, tag="_")

    def test_match(self, meta_data):

        tokens = linked_tokens(["A", "Madden"])

        assert self.pattern.match(tokens[0], meta_data) == (tokens[0], tokens[1])

    def test_lowercase_initial(self, meta_data):

        tokens = linked_tokens(["a", "Madden"])

        assert self.pattern.match(tokens[0], meta_data) is None

    def test_lowercase_name(self, meta_data):

        tokens = linked_tokens(["A", "madden"])

        assert self.pattern.match(tokens[0], meta_data) is None

    def test_short_name(self, meta_data):

        tokens = linked_tokens(["A", "Li"])

        assert self.pattern.match(tokens[0], meta_data) is None


class TestInitiaalInterfixCapitalPattern:

    pattern = InitiaalInterfixCapitalPattern(lookup_sets=lookup_sets, tag="_")

    def test_match(self, meta_data):

        tokens = linked_tokens(["A", "van der", "Steeg"])

        assert self.pattern.match(tokens[1], meta_data) == (tokens[0], tokens[2])

    def test_lowercase_initial(self, meta_data):

        tokens = linked_tokens(["a", "van der", "Steeg"])

        assert self.pattern.match(tokens[1], meta_data) is None

    def test_lowercase_name(self, meta_data):
        tokens = linked_tokens(["A", "van der", "steeg"])

        assert self.pattern.match(tokens[1], meta_data) is None


class TestFirstNameLookupPattern:

    pattern = FirstNameLookupPattern(lookup_sets=lookup_sets, tag="_")

    def test_pattern(self, meta_data):

        tokens = linked_tokens(["Soulaiman"])

        assert self.pattern.match(tokens[0], meta_data) == (tokens[0], tokens[0])

    def test_pattern_no_match(self, meta_data):

        tokens = linked_tokens(["Opnameafdeling"])

        assert self.pattern.match(tokens[0], meta_data) is None


class TestSurnameLookupPattern:

    pattern = SurnameLookupPattern(lookup_sets=lookup_sets, tag="_")

    def test_pattern(self, meta_data):

        tokens = linked_tokens(["Nguyen"])

        assert self.pattern.match(tokens[0], meta_data) == (tokens[0], tokens[0])

    def test_pattern_no_match(self, meta_data):

        tokens = linked_tokens(["Opnameafdeling"])

        assert self.pattern.match(tokens[0], meta_data) is None
