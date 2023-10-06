import docdeid as dd

from deduce.str import (
    Acronimify,
    FilterBasedOnLookupSet,
    RemoveValues,
    TakeLastToken,
    TitleCase,
    UpperCaseFirstChar,
)


class TestStr:
    def test_uppercase_first_char(self):

        processor = UpperCaseFirstChar()

        assert processor.process("test") == "Test"
        assert processor.process("Test") == "Test"
        assert processor.process("t") == "T"
        assert processor.process("T") == "T"
        assert processor.process("A3") == "A3"
        assert processor.process("a3") == "A3"

    def test_titlecase(self):
        processor = TitleCase()

        assert processor.process("test") == "Test"
        assert processor.process("Test") == "Test"
        assert processor.process("Test test") == "Test Test"
        assert processor.process("t") == "T"
        assert processor.process("T") == "T"
        assert processor.process("T t") == "T T"
        assert processor.process("A3") == "A3"
        assert processor.process("a3") == "A3"
        assert processor.process("a3 a4") == "A3 A4"

    def test_take_last_token(self):
        processor = TakeLastToken()

        assert processor.process("test") == "test"
        assert processor.process("dit is een test") == "test"
        assert processor.process("") == ""

    def test_remove_values(self):
        processor = RemoveValues(filter_values=["de", "het", "een"])

        assert processor.process("de boot") == "boot"
        assert processor.process("debiet") == "debiet"
        assert (
            processor.process("van het Schip") == "vanSchip"
        )  # TODO Is this intended?
        assert processor.process("nummer een") == "nummer"

    def test_acronimify(self):
        processor = Acronimify()

        assert processor.process("Elizabeth Tweesteden Ziekenhuis") == "ETZ"
        assert processor.process("Umcu") == "U"
        assert processor.process("Universitair Medisch Centrum Utrecht") == "UMCU"
        assert processor.process("universitair medisch centrum utrecht") == "umcu"

    def test_filter_based_on_lookupset(self):
        lookup_set = dd.ds.LookupSet()
        lookup_set.add_items_from_iterable(["arts", "bakker", "slager"])

        processor = FilterBasedOnLookupSet(filter_set=lookup_set)

        assert processor.filter("")
        assert processor.filter("visser")
        assert not processor.filter("arts")
        assert not processor.filter("bakker")
        assert not processor.filter("slager")
