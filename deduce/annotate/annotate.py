""" The annotate module contains the code for annotating text"""
import re
from collections import OrderedDict
from dataclasses import dataclass

import docdeid
from docdeid.annotate.annotator import (
    MultiTokenLookupAnnotator,
    RegexpAnnotator,
    TokenPatternAnnotator,
)
from docdeid.ds.lookup import LookupSet
from docdeid.str.processor import LowercaseString

import deduce.utility
from deduce.annotate.annotation_processing import PersonAnnotationConverter
from deduce.lookup.lookup_sets import get_lookup_sets
from deduce.pattern.name import (
    FirstNameLookupPattern,
    InitiaalInterfixCapitalPattern,
    InitialWithCapitalPattern,
    InterfixWithNamePattern,
    PersonFirstNamePattern,
    PersonGivenNamePattern,
    PersonInitialFromNamePattern,
    PersonInitialsPattern,
    PersonSurnamePattern,
    PrefixWithNamePattern,
    SurnameLookupPattern,
)
from deduce.pattern.name_context import (
    AnnotationContextPattern,
    InitialNameContextPattern,
    InitialsContextPattern,
    InterfixContextPattern,
    NexusContextPattern,
)
from deduce.tokenize.tokenizer import Tokenizer


def _initialize():

    lookup_sets = get_lookup_sets()

    merge_terms = LookupSet()
    merge_terms.add_items_from_iterable(["A1", "A2", "A3", "A4", "\n", "\r", "\t"])
    merge_terms += lookup_sets["interfixes"]
    merge_terms += lookup_sets["prefixes"]

    tokenizer = Tokenizer(merge_terms=merge_terms)

    return lookup_sets, tokenizer


_lookup_sets, tokenizer = _initialize()


@dataclass
class Person:
    first_names: list[str] = None
    initials: str = None
    surname: str = None
    given_name: str = None


NAME_PATTERNS = {
    "prefix_with_name": PrefixWithNamePattern(tag="prefix+naam", lookup_sets=_lookup_sets),
    "interfix_with_name": InterfixWithNamePattern(tag="interfix+naam", lookup_sets=_lookup_sets),
    "initial_with_capital": InitialWithCapitalPattern(tag="initiaal+naam", lookup_sets=_lookup_sets),
    "initial_interfix": InitiaalInterfixCapitalPattern(tag="initiaal+interfix+naam", lookup_sets=_lookup_sets),
    "first_name_lookup": FirstNameLookupPattern(tag="voornaam_onbekend", lookup_sets=_lookup_sets),
    "surname_lookup": SurnameLookupPattern(tag="achternaam_onbekend", lookup_sets=_lookup_sets),
    "person_first_name": PersonFirstNamePattern(tag="voornaam_patient"),
    "person_initial_from_name": PersonInitialFromNamePattern(tag="initiaal_patient"),
    "person_initials": PersonInitialsPattern(tag="initialen_patient"),
    "person_given_name": PersonGivenNamePattern(tag="roepnaam_patient"),
    "person_surname": PersonSurnamePattern(tag="achternaam_patient", tokenizer=tokenizer),
}

NAME_CONTEXT_PATTERNS = [
    InitialsContextPattern(tag="initiaal+{tag}", lookup_sets=_lookup_sets),
    InterfixContextPattern(tag="{tag}+interfix+achternaam", lookup_sets=_lookup_sets),
    InitialNameContextPattern(tag="{tag}+initiaalhoofdletternaam", lookup_sets=_lookup_sets),
    NexusContextPattern(tag="{tag}+en+hoofdletternaam"),
]

REGEPXS = {
    "altrecht": {
        "regexp_pattern": re.compile(r"[aA][lL][tT][rR][eE][cC][hH][tT]((\s[A-Z][\w]*)*)"),
        "tag": "instelling",
    },
    "street_with_number": {
        "regexp_pattern": re.compile(
            r"([A-Z]\w+(baan|bolwerk|dam|dijk|dreef|gracht|hof|kade|laan|markt|pad|park|"
            r"plantsoen|plein|singel|steeg|straat|weg)(\s(\d+){1,6}\w{0,2})?)(\W|$)"
        ),
        "tag": "locatie",
        "capturing_group": 1,
    },
    "postal_code": {
        "regexp_pattern": re.compile(r"(\d{4} (?!MG)[A-Z]{2}|\d{4}(?!mg|MG)[a-zA-Z]{2})(\W|$)"),
        "tag": "locatie",
        "capturing_group": 1,
    },
    "postbus": {"regexp_pattern": re.compile(r"([Pp]ostbus\s\d{5})"), "tag": "locatie"},
    "phone_1": {
        "regexp_pattern": re.compile(
            r"(((0)[1-9]{2}[0-9][-]?[1-9][0-9]{5})|((\+31|0|0031)[1-9][0-9][-]?[1-9][0-9]{6}))"
        ),
        "tag": "telefoonnummer",
    },
    "phone_2": {
        "regexp_pattern": re.compile(r"(((\+31|0|0031)6)[-]?[1-9][0-9]{7})"),
        "tag": "telefoonnummer",
    },
    "phone_3": {
        "regexp_pattern": re.compile(r"((\(\d{3}\)|\d{3})\s?\d{3}\s?\d{2}\s?\d{2})"),
        "tag": "telefoonnummer",
    },
    "patient_number": {"regexp_pattern": re.compile(r"\d{7}"), "tag": "patientnummer"},
    "date_1": {
        "regexp_pattern": re.compile(
            r"(([1-9]|0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012]|[1-9])([- /.]{,2}(\d{4}|\d{2}))?)(\D|$)"
        ),
        "tag": "datum",
        "capturing_group": 1,
    },
    "date_2": {
        "regexp_pattern": re.compile(
            r"(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|"
            r"november|december)([- /.]{,2}(\d{4}|\d{2}))?)(\D|$)"
        ),
        "tag": "datum",
        "capturing_group": 1,
    },
    "age": {
        "regexp_pattern": re.compile(r"(\d{1,3})([ -](jarige|jarig|jaar))"),
        "tag": "leeftijd",
        "capturing_group": 1,
    },
    "email": {
        "regexp_pattern": re.compile(
            r"([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)"
        ),
        "tag": "url",
    },
    "url_1": {
        "regexp_pattern": re.compile(
            r"((?!mailto:)"
            r"((?:http|https|ftp)://)"
            r"(?:\S+(?::\S*)?@)?(?:(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
            r"(\.(?:[0-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|((?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)"
            r"(?:\.(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)*(\.([a-z\u00a1-\uffff]{2,})))|localhost)"
            r"(?::\d{2,5})?(?:([/?#])[^\s]*)?)"
        ),
        "tag": "url",
    },
    "url_2": {
        "regexp_pattern": re.compile(r"([\w\d.-]{3,}(\.)(nl|com|net|be)(/[^\s]+)?)"),
        "tag": "url",
    },
}


class NamesContextAnnotator(docdeid.BaseAnnotator):
    """This needs to go after the relevant annotators."""

    def __init__(self, context_patterns: list[AnnotationContextPattern], tags: list[str]):
        self._context_patterns = context_patterns
        self._tags = tags
        super().__init__(tag=None)

    def _get_context_annotations(self, document: docdeid.Document) -> list[docdeid.Annotation]:

        annotations = [
            annotation for annotation in document.annotations if deduce.utility.any_in_text(self._tags, annotation.tag)
        ]

        return annotations

    def _annotate_context(
        self, annotations: list[docdeid.Annotation], doc: docdeid.Document
    ) -> list[docdeid.Annotation]:

        context_patterns = [pattern for pattern in self._context_patterns if pattern.document_precondition(doc)]

        next_annotations = []

        for annotation in annotations:

            new_annotation: docdeid.Annotation
            changes = False

            for context_pattern in context_patterns:

                if context_pattern.token_precondition(annotation.start_token, annotation.end_token):

                    match = context_pattern.match(annotation.start_token, annotation.end_token, annotation.tag)

                    if match is not None:

                        start_token, end_token = match

                        next_annotations.append(
                            docdeid.Annotation(
                                text=doc.text[start_token.start_char : end_token.end_char],
                                start_char=start_token.start_char,
                                end_char=end_token.end_char,
                                tag=context_pattern.tag.format(tag=annotation.tag),
                                start_token=start_token,
                                end_token=end_token,
                            )
                        )

                        changes = True
                        break

            if changes:
                continue
            else:
                next_annotations.append(annotation)

        # changes
        if set(annotations) != set(next_annotations):
            next_annotations = self._annotate_context(next_annotations, doc)

        return next_annotations

    def annotate(self, doc: docdeid.Document) -> set[docdeid.Annotation]:

        annotations = self._get_context_annotations(doc)

        for annotation in annotations:
            doc.annotations.remove(annotation)

        annotations = self._annotate_context(annotations, doc)

        return set(annotations)


def _get_name_pattern_annotators() -> OrderedDict[str, docdeid.DocProcessor]:

    annotators = OrderedDict()

    for pattern_name, pattern in NAME_PATTERNS.items():
        annotators[pattern_name] = TokenPatternAnnotator(pattern=pattern)

    return annotators


def _get_regexp_annotators() -> OrderedDict[str, docdeid.DocProcessor]:

    annotators = OrderedDict()

    for annotator_name, regexp_info in REGEPXS.items():
        annotators[annotator_name] = RegexpAnnotator(**regexp_info)

    return annotators


def _get_name_processor_group() -> docdeid.DocProcessorGroup:

    name_processors = _get_name_pattern_annotators()

    name_processors["name_context"] = NamesContextAnnotator(
        context_patterns=NAME_CONTEXT_PATTERNS, tags=["initia", "naam", "interfix", "prefix"]
    )

    name_processors["person_annotation_converter"] = PersonAnnotationConverter()

    return docdeid.DocProcessorGroup(name_processors)


def get_doc_processors() -> OrderedDict[str, docdeid.DocProcessor]:

    annotators = OrderedDict()

    annotators["name_group"] = _get_name_processor_group()

    annotators["institution"] = MultiTokenLookupAnnotator(
        lookup_values=_lookup_sets["institutions"],
        tokenizer=tokenizer,
        tag="instelling",
        matching_pipeline=[LowercaseString()],
        merge=False,
    )

    annotators["residence"] = MultiTokenLookupAnnotator(
        lookup_values=_lookup_sets["residences"],
        tokenizer=tokenizer,
        tag="locatie",
        merge=False,
    )

    annotators |= _get_regexp_annotators()

    return annotators
