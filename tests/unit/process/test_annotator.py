from unittest.mock import patch

import docdeid as dd
import pytest

from deduce.pattern.name_context import AnnotationContextPattern
from deduce.process.annotator import AnnotationContextPatternAnnotator, BsnAnnotator
from tests.helpers import link_tokens


@pytest.fixture
def bsn_doc():

    d = dd.DocDeid()

    return d.deidentify(
        text="Geldige voorbeelden zijn: 111222333 en 123456782. " "Patientnummer is 01234, en ander id 01234567890."
    )


class ExtendCapitalContextPattern(AnnotationContextPattern):
    def annotation_precondition(self, annotation: dd.Annotation) -> bool:
        return annotation.end_token.next() is not None

    def match(self, annotation: dd.Annotation):
        if annotation.end_token.next().text[0].isupper():
            return annotation.start_token, annotation.end_token.next()


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

        an = BsnAnnotator(tag="_")

        assert an._elfproef("111222333")
        assert not an._elfproef("111222334")
        assert an._elfproef("123456782")
        assert not an._elfproef("123456783")

    def test_elfproef_wrong_length(self):

        an = BsnAnnotator(tag="_")

        with pytest.raises(ValueError):
            an._elfproef("12345678")

    def test_elfproef_non_numeric(self):

        an = BsnAnnotator(tag="_")

        with pytest.raises(ValueError):
            an._elfproef("test")

    def test_annotate(self, bsn_doc):

        an = BsnAnnotator(tag="_")
        annotations = an.annotate(bsn_doc)

        expected_annotations = [
            dd.Annotation(text="111222333", start_char=26, end_char=35, tag="_"),
            dd.Annotation(text="123456782", start_char=39, end_char=48, tag="_"),
        ]

        assert annotations == expected_annotations
