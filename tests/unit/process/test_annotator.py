from unittest.mock import patch

import docdeid as dd
import pytest

from deduce.pattern.name_context import AnnotationContextPattern
from deduce.process.annotator import (
    AnnotationContextPatternAnnotator,
    BsnAnnotator,
    PhoneNumberAnnotator,
    TokenPatternAnnotator,
)
from deduce.tokenizer import DeduceTokenizer
from tests.helpers import link_tokens


@pytest.fixture
def ds():

    ds = dd.ds.DsCollection()

    first_names = ["Andries", "pieter", "Aziz", "Bernard"]
    surnames = ["Smit", "Bakker", "Heerma"]

    ds["first_names"] = dd.ds.LookupSet()
    ds["first_names"].add_items_from_iterable(items=first_names)

    ds["surnames"] = dd.ds.LookupSet()
    ds["surnames"].add_items_from_iterable(items=surnames)

    return ds


@pytest.fixture
def pattern_doc():

    return dd.Document(text="De man heet Andries Meijer, voornaam Andries.", tokenizers={"default": DeduceTokenizer()})


@pytest.fixture
def bsn_doc():

    d = dd.DocDeid()

    return d.deidentify(
        text="Geldige voorbeelden zijn: 111222333 en 123456782. " "Patientnummer is 01234, en ander id 01234567890."
    )


@pytest.fixture
def phone_number_doc():

    d = dd.DocDeid()

    return d.deidentify(
        text="Telefoonnummers zijn 0314-555555, (088 755 55 55) of (06)55555555, maar 065555 is "
        "te kort en 065555555555 is te lang. Verwijsnummer is 0800-9003."
    )


class ExtendCapitalContextPattern(AnnotationContextPattern):
    def annotation_precondition(self, annotation: dd.Annotation) -> bool:
        return annotation.end_token.next() is not None

    def match(self, annotation: dd.Annotation):
        if annotation.end_token.next().text[0].isupper():
            return annotation.start_token, annotation.end_token.next()


class TestTokenPatternAnnotator:
    def test_match_and(self):

        tpa = TokenPatternAnnotator(pattern=[{}], tag="_")
        assert tpa.match(
            dd.Token("Abcd", start_char=0, end_char=4), {"and": [{"min_len": 3}, {"starts_with_capital": True}]}
        )
        assert not tpa.match(
            dd.Token("abcd", start_char=0, end_char=4), {"and": [{"min_len": 3}, {"starts_with_capital": True}]}
        )
        assert not tpa.match(
            dd.Token("A", start_char=0, end_char=1), {"and": [{"min_len": 3}, {"starts_with_capital": True}]}
        )
        assert not tpa.match(
            dd.Token("a", start_char=0, end_char=1), {"and": [{"min_len": 3}, {"starts_with_capital": True}]}
        )

    def test_match_or(self):

        tpa = TokenPatternAnnotator(pattern=[{}], tag="_")
        assert tpa.match(
            dd.Token("Abcd", start_char=0, end_char=4), {"or": [{"min_len": 3}, {"starts_with_capital": True}]}
        )
        assert tpa.match(
            dd.Token("abcd", start_char=0, end_char=4), {"or": [{"min_len": 3}, {"starts_with_capital": True}]}
        )
        assert tpa.match(
            dd.Token("A", start_char=0, end_char=1), {"or": [{"min_len": 3}, {"starts_with_capital": True}]}
        )
        assert not tpa.match(
            dd.Token("a", start_char=0, end_char=1), {"or": [{"min_len": 3}, {"starts_with_capital": True}]}
        )

    def test_match_min_len(self):

        tpa = TokenPatternAnnotator(pattern=[{}], tag="_")

        assert tpa.match(dd.Token("abcd", start_char=0, end_char=4), {"min_len": 3})
        assert not tpa.match(dd.Token("a", start_char=0, end_char=1), {"min_len": 3})

    def test_match_starts_with_capital(self):

        tpa = TokenPatternAnnotator(pattern=[{}], tag="_")

        assert tpa.match(dd.Token("Abcd", start_char=0, end_char=4), {"starts_with_capital": True})
        assert not tpa.match(dd.Token("a", start_char=0, end_char=1), {"starts_with_capital": True})

    def test_match_is_initial(self):

        tpa = TokenPatternAnnotator(pattern=[{}], tag="_")

        assert tpa.match(dd.Token("A", start_char=0, end_char=1), {"is_initial": True})
        assert not tpa.match(dd.Token("a", start_char=0, end_char=1), {"is_initial": True})
        assert not tpa.match(dd.Token("Abcd", start_char=0, end_char=4), {"is_initial": True})

    def test_match_lookup(self, ds):

        tpa = TokenPatternAnnotator(pattern=[{}], ds=ds, tag="_")

        assert tpa.match(dd.Token("Andries", start_char=0, end_char=7), {"lookup": "first_names"})
        assert not tpa.match(dd.Token("andries", start_char=0, end_char=7), {"lookup": "first_names"})
        assert not tpa.match(dd.Token("Andries", start_char=0, end_char=7), {"lookup": "surnames"})
        assert not tpa.match(dd.Token("Smit", start_char=0, end_char=4), {"lookup": "first_names"})
        assert tpa.match(dd.Token("Smit", start_char=0, end_char=4), {"lookup": "surnames"})
        assert not tpa.match(dd.Token("smit", start_char=0, end_char=4), {"lookup": "surnames"})

    def test_match_neg_lookup(self, ds):

        tpa = TokenPatternAnnotator(pattern=[{}], ds=ds, tag="_")

        assert not tpa.match(dd.Token("Andries", start_char=0, end_char=7), {"neg_lookup": "first_names"})
        assert tpa.match(dd.Token("andries", start_char=0, end_char=7), {"neg_lookup": "first_names"})
        assert tpa.match(dd.Token("Andries", start_char=0, end_char=7), {"neg_lookup": "surnames"})
        assert tpa.match(dd.Token("Smit", start_char=0, end_char=4), {"neg_lookup": "first_names"})
        assert not tpa.match(dd.Token("Smit", start_char=0, end_char=4), {"neg_lookup": "surnames"})
        assert tpa.match(dd.Token("smit", start_char=0, end_char=4), {"neg_lookup": "surnames"})

    def test_match_lowercase_lookup(self, ds):

        tpa = TokenPatternAnnotator(pattern=[{}], ds=ds, tag="_")

        assert tpa.match(dd.Token("Pieter", start_char=0, end_char=6), {"lowercase_lookup": "first_names"})
        assert tpa.match(dd.Token("pieter", start_char=0, end_char=6), {"lowercase_lookup": "first_names"})
        assert not tpa.match(dd.Token("smit", start_char=0, end_char=4), {"lowercase_lookup": "first_names"})

    def test_match_sequence(self, pattern_doc, ds):

        pattern = [{"lookup": "first_names"}, {"starts_with_capital": True}]

        tpa = TokenPatternAnnotator(pattern=[{}], ds=ds, tag="_")

        assert tpa.match_sequence(
            pattern_doc, start_token=pattern_doc.get_tokens()[3], pattern=pattern
        ) == dd.Annotation(text="Andries Meijer", start_char=12, end_char=26, tag="_")
        assert tpa.match_sequence(pattern_doc, start_token=pattern_doc.get_tokens()[7], pattern=pattern) is None

    def test_annotate(self, pattern_doc, ds):

        pattern = [{"lookup": "first_names"}, {"starts_with_capital": True}]

        tpa = TokenPatternAnnotator(pattern=pattern, ds=ds, tag="_")

        assert tpa.annotate(pattern_doc) == [dd.Annotation(text="Andries Meijer", start_char=12, end_char=26, tag="_")]


class TestContextPatternsAnnotator:
    def test_tags(self):
        annotations = [
            dd.Annotation(text="_", start_char=0, end_char=1, tag="voornaam"),
            dd.Annotation(text="_", start_char=0, end_char=1, tag="achternaam"),
            dd.Annotation(text="_", start_char=0, end_char=1, tag="voornaam_patient"),
        ]

        input_annotations = dd.AnnotationSet(annotations)
        expected_annotations = dd.AnnotationSet([annotations[0], annotations[2]])

        annotator = AnnotationContextPatternAnnotator(context_patterns=[], tags=["voornaam"])

        assert dd.AnnotationSet(annotator.get_matching_tag_annotations(list(input_annotations))) == expected_annotations

    def test_tags_none(self):
        annotations = [
            dd.Annotation(text="_", start_char=0, end_char=1, tag="voornaam"),
            dd.Annotation(text="_", start_char=0, end_char=1, tag="achternaam"),
            dd.Annotation(text="_", start_char=0, end_char=1, tag="voornaam_patient"),
        ]

        input_annotations = dd.AnnotationSet(annotations)

        annotator = AnnotationContextPatternAnnotator(context_patterns=[], tags=None)

        assert dd.AnnotationSet(annotator.get_matching_tag_annotations(list(input_annotations))) == input_annotations

    def test_annotate(self):
        annotations_input = [
            dd.Annotation(text="_", start_char=0, end_char=1, tag="voornaam"),
            dd.Annotation(text="_", start_char=0, end_char=1, tag="achternaam"),
            dd.Annotation(text="_", start_char=0, end_char=1, tag="voornaam_patient"),
        ]

        annotations_output = [
            annotations_input[0],
            annotations_input[1],
            dd.Annotation(text="_", start_char=0, end_char=1, tag="voornaam_patient+achternaam_patient"),
        ]

        doc = dd.Document(text="_")
        doc.annotations = dd.AnnotationSet(annotations_input)

        annotator = AnnotationContextPatternAnnotator(context_patterns=[], tags=["voornaam_patient"])

        with patch.object(annotator, "_annotate_context", return_value=dd.AnnotationSet(annotations_output)):
            context_annotations = annotator.annotate(doc)

        assert annotations_input[0] in doc.annotations
        assert annotations_input[1] in doc.annotations
        assert annotations_input[2] not in doc.annotations
        assert annotations_output[2] in context_annotations

    @patch("deduce.pattern.name_context.AnnotationContextPattern.__abstractmethods__", set())
    def test_doc_precondition(self):
        pattern1 = AnnotationContextPattern(tag="_")
        pattern2 = AnnotationContextPattern(tag="_")
        annotator = AnnotationContextPatternAnnotator(context_patterns=[pattern1, pattern2])
        doc = dd.Document(text="_")
        doc.annotations = dd.AnnotationSet([dd.Annotation(text="_", start_char=0, end_char=1, tag="_")])

        with patch.object(pattern1, "document_precondition", return_value=True), patch.object(
            pattern1, "match", return_value=None
        ) as p1_match, patch.object(pattern2, "document_precondition", return_value=False), patch.object(
            pattern2, "match", return_value=None
        ) as p2_match:

            annotator.annotate(doc)

            p1_match.assert_called_once()
            p2_match.assert_not_called()

    @patch("deduce.pattern.name_context.AnnotationContextPattern.__abstractmethods__", set())
    def test_annotation_precondition(self):
        pattern1 = AnnotationContextPattern(tag="_")
        annotator = AnnotationContextPatternAnnotator(context_patterns=[pattern1])
        doc = dd.Document(text="_")
        annotations = [
            dd.Annotation(text="a", start_char=0, end_char=1, tag="_"),
            dd.Annotation(text="b", start_char=0, end_char=1, tag="_"),
            dd.Annotation(text="c", start_char=0, end_char=1, tag="_"),
        ]
        doc.annotations = dd.AnnotationSet(annotations)

        with patch.object(
            pattern1, "annotation_precondition", side_effect=lambda x: x == annotations[0]
        ) as p1_annotation_precond, patch.object(pattern1, "match", return_value=None) as p1_match:

            annotator.annotate(doc)

            assert p1_annotation_precond.call_count == len(annotations)
            assert p1_match.call_count == 1

    def test_annotate_context(self):
        annotator = AnnotationContextPatternAnnotator(
            context_patterns=[ExtendCapitalContextPattern(tag="{tag}+hoofdletter")], iterative=False
        )

        tokens = link_tokens(
            [
                dd.Token("Marjon", start_char=0, end_char=6),
                dd.Token("Ghislaine", start_char=7, end_char=16),
                dd.Token("Pater", start_char=17, end_char=22),
            ]
        )

        doc = dd.Document(text="Marjon Ghislaine Pater")
        doc.annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Marjon", start_char=0, end_char=6, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
                )
            ]
        )

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Marjon Ghislaine",
                    start_char=0,
                    end_char=16,
                    tag="voornaam+hoofdletter",
                    start_token=tokens[0],
                    end_token=tokens[1],
                )
            ]
        )

        context_annotations = annotator._annotate_context(list(doc.annotations), doc)

        assert dd.AnnotationSet(context_annotations) == expected_annotations

    def test_annotate_context_iterative(self):
        annotator = AnnotationContextPatternAnnotator(
            context_patterns=[ExtendCapitalContextPattern(tag="{tag}+hoofdletter")], iterative=True
        )

        tokens = link_tokens(
            [
                dd.Token("Marjon", start_char=0, end_char=6),
                dd.Token("Ghislaine", start_char=7, end_char=16),
                dd.Token("Pater", start_char=17, end_char=22),
            ]
        )

        doc = dd.Document(text="Marjon Ghislaine Pater")
        doc.annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Marjon", start_char=0, end_char=6, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
                )
            ]
        )

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Marjon Ghislaine Pater",
                    start_char=0,
                    end_char=22,
                    tag="voornaam+hoofdletter+hoofdletter",
                    start_token=tokens[0],
                    end_token=tokens[2],
                )
            ]
        )

        context_annotations = annotator._annotate_context(list(doc.annotations), doc)

        assert dd.AnnotationSet(context_annotations) == expected_annotations

    def test_annotate_context_multiple(self):
        annotator = AnnotationContextPatternAnnotator(
            context_patterns=[ExtendCapitalContextPattern(tag="{tag}+hoofdletter")], iterative=False
        )

        tokens = link_tokens(
            [
                dd.Token("Marjon", start_char=0, end_char=6),
                dd.Token("Ghislaine", start_char=7, end_char=16),
                dd.Token("Pater", start_char=17, end_char=22),
            ]
        )

        doc = dd.Document(text="Marjon Ghislaine Pater")
        doc.annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Marjon", start_char=0, end_char=6, tag="voornaam", start_token=tokens[0], end_token=tokens[0]
                ),
                dd.Annotation(
                    text="Ghislaine",
                    start_char=7,
                    end_char=16,
                    tag="achternaam",
                    start_token=tokens[1],
                    end_token=tokens[1],
                ),
            ]
        )

        expected_annotations = dd.AnnotationSet(
            [
                dd.Annotation(
                    text="Marjon Ghislaine",
                    start_char=0,
                    end_char=16,
                    tag="voornaam+hoofdletter",
                    start_token=tokens[0],
                    end_token=tokens[1],
                ),
                dd.Annotation(
                    text="Ghislaine Pater",
                    start_char=7,
                    end_char=22,
                    tag="achternaam+hoofdletter",
                    start_token=tokens[1],
                    end_token=tokens[2],
                ),
            ]
        )

        context_annotations = annotator._annotate_context(list(doc.annotations), doc)

        assert dd.AnnotationSet(context_annotations) == expected_annotations


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


class TestPhoneNumberAnnotator:
    def test_annotate_defaults(self, phone_number_doc):

        an = PhoneNumberAnnotator(
            phone_regexp=r"(?<!\d)"
            r"(\(?(0031|\+31|0)(1[035]|2[0347]|3[03568]|4[03456]|5[0358]|6|7|88|800|91|90[069]|[1-5]\d{2})\)?)"
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
            r"(\(?(0031|\+31|0)(1[035]|2[0347]|3[03568]|4[03456]|5[0358]|6|7|88|800|91|90[069]|[1-5]\d{2})\)?)"
            r" ?-? ?"
            r"((\d{2,4}[ -]?)+\d{2,4})",
            min_digits=4,
            max_digits=8,
            tag="_",
        )
        annotations = an.annotate(phone_number_doc)

        expected_annotations = [dd.Annotation(text="065555", start_char=72, end_char=78, tag="_")]

        assert annotations == expected_annotations

    def test_annotate_long(self, phone_number_doc):

        an = PhoneNumberAnnotator(
            phone_regexp=r"(?<!\d)"
            r"(\(?(0031|\+31|0)(1[035]|2[0347]|3[03568]|4[03456]|5[0358]|6|7|88|800|91|90[069]|[1-5]\d{2})\)?)"
            r" ?-? ?"
            r"((\d{2,4}[ -]?)+\d{2,4})",
            min_digits=11,
            max_digits=12,
            tag="_",
        )
        annotations = an.annotate(phone_number_doc)

        expected_annotations = [dd.Annotation(text="065555555555", start_char=93, end_char=105, tag="_")]

        assert annotations == expected_annotations
