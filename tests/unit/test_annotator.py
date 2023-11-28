import re

import docdeid as dd
import pytest

from deduce.annotator import (
    BsnAnnotator,
    ContextAnnotator,
    PhoneNumberAnnotator,
    RegexpPseudoAnnotator,
    TokenPatternAnnotator,
    _PatternPositionMatcher,
)
from deduce.tokenizer import DeduceTokenizer


@pytest.fixture
def ds():
    ds = dd.ds.DsCollection()

    first_names = ["Andries", "pieter", "Aziz", "Bernard"]
    surnames = ["Meijer", "Smit", "Bakker", "Heerma"]

    ds["first_names"] = dd.ds.LookupSet()
    ds["first_names"].add_items_from_iterable(items=first_names)

    ds["surnames"] = dd.ds.LookupSet()
    ds["surnames"].add_items_from_iterable(items=surnames)

    return ds


@pytest.fixture
def regexp_pseudo_doc():

    return dd.Document(
        text="De patient is Na 12 jaar gestopt met medicijnen.",
        tokenizers={"default": DeduceTokenizer()},
    )


@pytest.fixture
def pattern_doc():
    return dd.Document(
        text="De man heet Andries Meijer-Heerma, voornaam Andries.",
        tokenizers={"default": DeduceTokenizer()},
    )


@pytest.fixture
def bsn_doc():
    d = dd.DocDeid()

    return d.deidentify(
        text="Geldige voorbeelden zijn: 111222333 en 123456782. "
        "Patientnummer is 01234, en ander id 01234567890."
    )


@pytest.fixture
def phone_number_doc():
    d = dd.DocDeid()

    return d.deidentify(
        text="Telefoonnummers zijn 0314-555555, (088 755 55 55) of (06)55555555, "
        "maar 065555 is te kort en 065555555555 is te lang. "
        "Verwijsnummer is 0800-9003."
    )


def token(text: str):
    return dd.Token(text=text, start_char=0, end_char=len(text))


class TestPatternPositionMatcher:
    def test_equal(self):
        assert _PatternPositionMatcher.match({"equal": "test"}, token=token("test"))
        assert not _PatternPositionMatcher.match({"equal": "_"}, token=token("test"))

    def test_re_match(self):
        assert _PatternPositionMatcher.match({"re_match": "[a-z]"}, token=token("abc"))
        assert _PatternPositionMatcher.match(
            {"re_match": "[a-z]"}, token=token("abc123")
        )
        assert not _PatternPositionMatcher.match({"re_match": "[a-z]"}, token=token(""))
        assert not _PatternPositionMatcher.match(
            {"re_match": "[a-z]"}, token=token("123")
        )
        assert not _PatternPositionMatcher.match(
            {"re_match": "[a-z]"}, token=token("123abc")
        )

    def test_match_is_initial(self):
        pattern_position = {"is_initial": True}

        assert _PatternPositionMatcher.match(pattern_position, token=token("A"))
        assert _PatternPositionMatcher.match(pattern_position, token=token("Ch"))
        assert _PatternPositionMatcher.match(pattern_position, token=token("Chr"))
        assert _PatternPositionMatcher.match(pattern_position, token=token("Ph"))
        assert _PatternPositionMatcher.match(pattern_position, token=token("Th"))
        assert not _PatternPositionMatcher.match(pattern_position, token=token("a"))
        assert not _PatternPositionMatcher.match(pattern_position, token=token("Ah"))
        assert not _PatternPositionMatcher.match(pattern_position, token=token("Abcd"))

    def test_match_like_name(self):
        pattern_position = {"like_name": True}

        assert _PatternPositionMatcher.match(pattern_position, token=token("Diederik"))
        assert not _PatternPositionMatcher.match(pattern_position, token=token("Le"))
        assert not _PatternPositionMatcher.match(
            pattern_position, token=token("diederik")
        )
        assert not _PatternPositionMatcher.match(
            pattern_position, token=token("Diederik3")
        )

    def test_match_lookup(self, ds):
        assert _PatternPositionMatcher.match(
            {"lookup": "first_names"}, token=token("Andries"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"lookup": "first_names"}, token=token("andries"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"lookup": "surnames"}, token=token("Andries"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"lookup": "first_names"}, token=token("Smit"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"lookup": "surnames"}, token=token("Smit"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"lookup": "surnames"}, token=token("smit"), ds=ds
        )

    def test_match_neg_lookup(self, ds):
        assert not _PatternPositionMatcher.match(
            {"neg_lookup": "first_names"}, token=token("Andries"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"neg_lookup": "first_names"}, token=token("andries"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"neg_lookup": "surnames"}, token=token("Andries"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"neg_lookup": "first_names"}, token=token("Smit"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"neg_lookup": "surnames"}, token=token("Smit"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"neg_lookup": "surnames"}, token=token("smit"), ds=ds
        )

    def test_match_lowercase_lookup(self, ds):
        assert _PatternPositionMatcher.match(
            {"lowercase_lookup": "first_names"}, token=token("Pieter"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"lowercase_lookup": "first_names"}, token=token("pieter"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"lowercase_lookup": "first_names"}, token=token("smit"), ds=ds
        )

    def test_match_lowercase_neg_lookup(self, ds):
        assert _PatternPositionMatcher.match(
            {"lowercase_neg_lookup": "first_names"}, token=token("Andries"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"lowercase_neg_lookup": "first_names"}, token=token("andries"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"lowercase_neg_lookup": "first_names"}, token=token("pieter"), ds=ds
        )

    def test_match_and(self):
        assert _PatternPositionMatcher.match(
            {"and": [{"equal": "Abcd"}, {"like_name": True}]},
            token=token("Abcd"),
            ds=ds,
        )
        assert not _PatternPositionMatcher.match(
            {"and": [{"equal": "dcef"}, {"like_name": True}]},
            token=token("Abcd"),
            ds=ds,
        )
        assert not _PatternPositionMatcher.match(
            {"and": [{"equal": "A"}, {"like_name": True}]}, token=token("A"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"and": [{"equal": "b"}, {"like_name": True}]}, token=token("a"), ds=ds
        )

    def test_match_or(self):
        assert _PatternPositionMatcher.match(
            {"or": [{"equal": "Abcd"}, {"like_name": True}]}, token=token("Abcd"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"or": [{"equal": "dcef"}, {"like_name": True}]}, token=token("Abcd"), ds=ds
        )
        assert _PatternPositionMatcher.match(
            {"or": [{"equal": "A"}, {"like_name": True}]}, token=token("A"), ds=ds
        )
        assert not _PatternPositionMatcher.match(
            {"or": [{"equal": "b"}, {"like_name": True}]}, token=token("a"), ds=ds
        )


class TestTokenPatternAnnotator:
    def test_match_sequence(self, pattern_doc, ds):
        pattern = [{"lookup": "first_names"}, {"like_name": True}]

        tpa = TokenPatternAnnotator(pattern=[{}], ds=ds, tag="_")

        assert tpa._match_sequence(
            pattern_doc, start_token=pattern_doc.get_tokens()[3], pattern=pattern
        ) == dd.Annotation(text="Andries Meijer", start_char=12, end_char=26, tag="_")
        assert (
            tpa._match_sequence(
                pattern_doc, start_token=pattern_doc.get_tokens()[7], pattern=pattern
            )
            is None
        )

    def test_match_sequence_left(self, pattern_doc, ds):
        pattern = [{"lookup": "first_names"}, {"like_name": True}]

        tpa = TokenPatternAnnotator(pattern=[{}], ds=ds, tag="_")

        assert tpa._match_sequence(
            pattern_doc,
            start_token=pattern_doc.get_tokens()[4],
            pattern=pattern,
            direction="left",
        ) == dd.Annotation(text="Andries Meijer", start_char=12, end_char=26, tag="_")

        assert (
            tpa._match_sequence(
                pattern_doc,
                start_token=pattern_doc.get_tokens()[8],
                direction="left",
                pattern=pattern,
            )
            is None
        )

    def test_match_sequence_skip(self, pattern_doc, ds):
        pattern = [{"lookup": "surnames"}, {"like_name": True}]

        tpa = TokenPatternAnnotator(pattern=[{}], ds=ds, tag="_")

        assert tpa._match_sequence(
            pattern_doc,
            start_token=pattern_doc.get_tokens()[4],
            pattern=pattern,
            skip={"-"},
        ) == dd.Annotation(text="Meijer-Heerma", start_char=20, end_char=33, tag="_")
        assert (
            tpa._match_sequence(
                pattern_doc,
                start_token=pattern_doc.get_tokens()[4],
                pattern=pattern,
                skip=[],
            )
            is None
        )

    def test_annotate(self, pattern_doc, ds):
        pattern = [{"lookup": "first_names"}, {"like_name": True}]

        tpa = TokenPatternAnnotator(pattern=pattern, ds=ds, tag="_")

        assert tpa.annotate(pattern_doc) == [
            dd.Annotation(text="Andries Meijer", start_char=12, end_char=26, tag="_")
        ]


class TestContextAnnotator:
    def test_apply_context_pattern(self, pattern_doc):
        annotator = ContextAnnotator(pattern=[])

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Andries",
                    start_char=12,
                    end_char=19,
                    tag="voornaam",
                    start_token=pattern_doc.get_tokens()[3],
                    end_token=pattern_doc.get_tokens()[3],
                )
            ]
        )

        assert annotator._apply_context_pattern(
            pattern_doc,
            annotations,
            {
                "pattern": [{"like_name": True}],
                "direction": "right",
                "pre_tag": "voornaam",
                "tag": "{tag}+naam",
            },
        ) == dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Andries Meijer",
                    start_char=12,
                    end_char=26,
                    tag="voornaam+naam",
                )
            ]
        )

    def test_apply_context_pattern_left(self, pattern_doc):
        annotator = ContextAnnotator(pattern=[])

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Meijer",
                    start_char=20,
                    end_char=26,
                    tag="achternaam",
                    start_token=pattern_doc.get_tokens()[4],
                    end_token=pattern_doc.get_tokens()[4],
                )
            ]
        )

        assert annotator._apply_context_pattern(
            pattern_doc,
            annotations,
            {
                "pattern": [{"like_name": True}],
                "direction": "left",
                "pre_tag": "achternaam",
                "tag": "naam+{tag}",
            },
        ) == dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Andries Meijer",
                    start_char=12,
                    end_char=26,
                    tag="naam+achternaam",
                )
            ]
        )

    def test_apply_context_pattern_skip(self, pattern_doc):
        annotator = ContextAnnotator(pattern=[])

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Meijer",
                    start_char=20,
                    end_char=26,
                    tag="achternaam",
                    start_token=pattern_doc.get_tokens()[4],
                    end_token=pattern_doc.get_tokens()[4],
                )
            ]
        )

        assert annotator._apply_context_pattern(
            pattern_doc,
            annotations,
            {
                "pattern": [{"like_name": True}],
                "direction": "right",
                "skip": ["-"],
                "pre_tag": "achternaam",
                "tag": "{tag}+naam",
            },
        ) == dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Meijer-Heerma",
                    start_char=20,
                    end_char=33,
                    tag="achternaam+naam",
                )
            ]
        )

    def test_annotate_multiple(self, pattern_doc):
        pattern = [
            {
                "pattern": [{"like_name": True}],
                "direction": "right",
                "pre_tag": "voornaam",
                "tag": "{tag}+naam",
            },
            {
                "pattern": [{"like_name": True}],
                "direction": "right",
                "skip": ["-"],
                "pre_tag": "achternaam",
                "tag": "{tag}+naam",
            },
        ]

        annotator = ContextAnnotator(pattern=pattern, iterative=False)

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Andries",
                    start_char=12,
                    end_char=19,
                    tag="voornaam",
                    start_token=pattern_doc.get_tokens()[3],
                    end_token=pattern_doc.get_tokens()[3],
                )
            ]
        )

        assert annotator._annotate(pattern_doc, annotations) == dd.AnnotationSet(
            {
                dd.Annotation(
                    text="Andries Meijer-Heerma",
                    start_char=12,
                    end_char=33,
                    tag="voornaam+naam+naam",
                )
            }
        )

    def test_annotate_iterative(self, pattern_doc):
        pattern = [
            {
                "pattern": [{"like_name": True}],
                "direction": "right",
                "skip": ["-"],
                "pre_tag": "naam",
                "tag": "{tag}+naam",
            }
        ]

        annotator = ContextAnnotator(pattern=pattern, iterative=True)

        annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Andries",
                    start_char=12,
                    end_char=19,
                    tag="voornaam",
                    start_token=pattern_doc.get_tokens()[3],
                    end_token=pattern_doc.get_tokens()[3],
                )
            ]
        )

        assert annotator._annotate(pattern_doc, annotations) == dd.AnnotationSet(
            {
                dd.Annotation(
                    text="Andries Meijer-Heerma",
                    start_char=12,
                    end_char=33,
                    tag="voornaam+naam+naam",
                )
            }
        )


class TestRegexpPseudoAnnotator:
    def test_is_word_char(self):

        assert RegexpPseudoAnnotator._is_word_char("a")
        assert RegexpPseudoAnnotator._is_word_char("abc")
        assert not RegexpPseudoAnnotator._is_word_char("123")
        assert not RegexpPseudoAnnotator._is_word_char(" ")
        assert not RegexpPseudoAnnotator._is_word_char("\n")
        assert not RegexpPseudoAnnotator._is_word_char(".")

    def test_get_previous_word(self):

        r = RegexpPseudoAnnotator(regexp_pattern="_", tag="_")

        assert r._get_previous_word(0, "12 jaar") == ""
        assert r._get_previous_word(1, "<12 jaar") == ""
        assert r._get_previous_word(8, "patient 12 jaar") == "patient"
        assert r._get_previous_word(7, "(sinds 12 jaar)") == "sinds"
        assert r._get_previous_word(11, "patient is 12 jaar)") == "is"

    def test_get_next(self):

        r = RegexpPseudoAnnotator(regexp_pattern="_", tag="_")

        assert r._get_next_word(7, "12 jaar") == ""
        assert r._get_next_word(7, "12 jaar, geleden") == ""
        assert r._get_next_word(7, "12 jaar geleden") == "geleden"
        assert r._get_next_word(7, "12 jaar geleden geopereerd") == "geleden"

    def test_validate_match(self, regexp_pseudo_doc):

        r = RegexpPseudoAnnotator(regexp_pattern="_", tag="_")
        pattern = re.compile(r"\d+ jaar")

        match = list(pattern.finditer(regexp_pseudo_doc.text))[0]

        assert r._validate_match(match, regexp_pseudo_doc)

    def test_validate_match_pre(self, regexp_pseudo_doc):

        r = RegexpPseudoAnnotator(
            regexp_pattern="_", tag="_", pre_pseudo=["sinds", "al", "vanaf"]
        )
        pattern = re.compile(r"\d+ jaar")

        match = list(pattern.finditer(regexp_pseudo_doc.text))[0]

        assert r._validate_match(match, regexp_pseudo_doc)

    def test_validate_match_post(self, regexp_pseudo_doc):

        r = RegexpPseudoAnnotator(
            regexp_pattern="_", tag="_", post_pseudo=["geleden", "getrouwd", "gestopt"]
        )
        pattern = re.compile(r"\d+ jaar")

        match = list(pattern.finditer(regexp_pseudo_doc.text))[0]

        assert not r._validate_match(match, regexp_pseudo_doc)

    def test_validate_match_lower(self, regexp_pseudo_doc):

        r = RegexpPseudoAnnotator(
            regexp_pattern="_", tag="_", pre_pseudo=["na"], lowercase=True
        )
        pattern = re.compile(r"\d+ jaar")

        match = list(pattern.finditer(regexp_pseudo_doc.text))[0]

        assert not r._validate_match(match, regexp_pseudo_doc)


class TestBsnAnnotator:
    def test_elfproef(self):
        an = BsnAnnotator(bsn_regexp="(\\D|^)(\\d{9})(\\D|$)", capture_group=2, tag="_")

        assert an._elfproef("111222333")
        assert not an._elfproef("111222334")
        assert an._elfproef("123456782")
        assert not an._elfproef("123456783")

    def test_elfproef_wrong_length(self):
        an = BsnAnnotator(bsn_regexp="(\\D|^)(\\d{9})(\\D|$)", capture_group=2, tag="_")

        with pytest.raises(ValueError):
            an._elfproef("12345678")

    def test_elfproef_non_numeric(self):
        an = BsnAnnotator(bsn_regexp="(\\D|^)(\\d{9})(\\D|$)", capture_group=2, tag="_")

        with pytest.raises(ValueError):
            an._elfproef("test")

    def test_annotate(self, bsn_doc):
        an = BsnAnnotator(bsn_regexp="(\\D|^)(\\d{9})(\\D|$)", capture_group=2, tag="_")
        annotations = an.annotate(bsn_doc)

        expected_annotations = [
            dd.Annotation(text="111222333", start_char=26, end_char=35, tag="_"),
            dd.Annotation(text="123456782", start_char=39, end_char=48, tag="_"),
        ]

        assert annotations == expected_annotations

    def test_annotate_with_nondigits(self, bsn_doc):
        an = BsnAnnotator(bsn_regexp=r"\d{4}\.\d{2}\.\d{3}", tag="_")
        doc = dd.Document("1234.56.782")
        annotations = an.annotate(doc)

        expected_annotations = [
            dd.Annotation(text="1234.56.782", start_char=0, end_char=11, tag="_"),
        ]

        assert annotations == expected_annotations


class TestPhoneNumberAnnotator:
    def test_annotate_defaults(self, phone_number_doc):
        an = PhoneNumberAnnotator(
            phone_regexp=r"(?<!\d)"
            r"(\(?(0031|\+31|0)"
            r"(1[035]|2[0347]|3[03568]|4[03456]|5[0358]|6|7|88|800|91|90[069]|"
            r"[1-5]\d{2})\)?)"
            r" ?-? ?"
            r"((\d{2,4}[ -]?)+\d{2,4})",
            tag="_",
        )
        annotations = an.annotate(phone_number_doc)

        expected_annotations = [
            dd.Annotation(text="0314-555555", start_char=21, end_char=32, tag="_"),
            dd.Annotation(text="088 755 55 55", start_char=35, end_char=48, tag="_"),
            dd.Annotation(text="(06)55555555", start_char=53, end_char=65, tag="_"),
            dd.Annotation(text="0800-9003", start_char=135, end_char=144, tag="_"),
        ]

        assert annotations == expected_annotations

    def test_annotate_short(self, phone_number_doc):
        an = PhoneNumberAnnotator(
            phone_regexp=r"(?<!\d)"
            r"(\(?(0031|\+31|0)"
            r"(1[035]|2[0347]|3[03568]|4[03456]|5[0358]|6|7|88|800|91|90[069]|"
            r"[1-5]\d{2})\)?)"
            r" ?-? ?"
            r"((\d{2,4}[ -]?)+\d{2,4})",
            min_digits=4,
            max_digits=8,
            tag="_",
        )
        annotations = an.annotate(phone_number_doc)

        expected_annotations = [
            dd.Annotation(text="065555", start_char=72, end_char=78, tag="_")
        ]

        assert annotations == expected_annotations

    def test_annotate_long(self, phone_number_doc):
        an = PhoneNumberAnnotator(
            phone_regexp=r"(?<!\d)"
            r"(\(?(0031|\+31|0)"
            r"(1[035]|2[0347]|3[03568]|4[03456]|5[0358]|6|7|88|800|91|90[069]|"
            r"[1-5]\d{2})\)?)"
            r" ?-? ?"
            r"((\d{2,4}[ -]?)+\d{2,4})",
            min_digits=11,
            max_digits=12,
            tag="_",
        )
        annotations = an.annotate(phone_number_doc)

        expected_annotations = [
            dd.Annotation(text="065555555555", start_char=93, end_char=105, tag="_")
        ]

        assert annotations == expected_annotations
