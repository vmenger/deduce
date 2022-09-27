""" The annotate module contains the code for annotating text"""
import re
from dataclasses import dataclass

import docdeid
from docdeid.annotate.annotation_processor import OverlapResolver
from docdeid.annotate.annotator import MultiTokenLookupAnnotator, RegexpAnnotator
from docdeid.ds.lookup import LookupList
from docdeid.str.processor import LowercaseString

from deduce.lookup.lookup_lists import get_lookup_lists
from deduce.patterns.name import (
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
    TokenPatternAnnotator,
)
from deduce.patterns.name_context import (
    InitialNameContextPattern,
    InitialsContextPattern,
    InterfixContextPattern,
    NexusContextPattern,
)
from deduce.tokenizer import Tokenizer
import deduce.utility

def _initialize():

    lookup_lists = get_lookup_lists()

    merge_terms = LookupList()
    merge_terms.add_items_from_iterable(["A1", "A2", "A3", "A4", "\n", "\r", "\t"])
    merge_terms += lookup_lists["interfixes"]
    merge_terms += lookup_lists["prefixes"]

    tokenizer = Tokenizer(merge_terms=merge_terms)

    return lookup_lists, tokenizer


_lookup_lists, tokenizer = _initialize()


@dataclass
class Person:
    first_names: list[str] = None
    initials: str = None
    surname: str = None
    given_name: str = None


NAME_PATTERNS = {
    'prefix_with_name': PrefixWithNamePattern(tag="prefix+naam", lookup_lists=_lookup_lists),
    'interfix_with_name': InterfixWithNamePattern(tag="interfix+naam", lookup_lists=_lookup_lists),
    'initial_with_capital': InitialWithCapitalPattern(tag="initiaal+naam", lookup_lists=_lookup_lists),
    'initial_interfix': InitiaalInterfixCapitalPattern(tag="initiaal+interfix+naam", lookup_lists=_lookup_lists),
    'first_name_lookup': FirstNameLookupPattern(tag="voornaam_onbekend", lookup_lists=_lookup_lists),
    'surname_lookup': SurnameLookupPattern(tag="achternaam_onbekend", lookup_lists=_lookup_lists),
    'person_first_name': PersonFirstNamePattern(tag="voornaam_patient"),
    'person_initial_from_name': PersonInitialFromNamePattern(tag="initiaal_patient"),
    'person_initials': PersonInitialsPattern(tag="initialen_patient"),
    'person_given_name': PersonGivenNamePattern(tag="roepnaam_patient"),
    'person_surname': PersonSurnamePattern(tag="achternaam_patient", tokenizer=tokenizer),
}


REGEPXS = {
    "altrecht": {
        "regexp_pattern": re.compile(
            r"[aA][lL][tT][rR][eE][cC][hH][tT]((\s[A-Z][\w]*)*)"
        ),
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
        "regexp_pattern": re.compile(
            r"(\d{4} (?!MG)[A-Z]{2}|\d{4}(?!mg|MG)[a-zA-Z]{2})(\W|$)"
        ),
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
    """ This needs to go after the relevant annotators."""

    def __init__(self):

        self._context_patterns = [
            InitialsContextPattern(lookup_lists=_lookup_lists),
            InterfixContextPattern(lookup_lists=_lookup_lists),
            InitialNameContextPattern(lookup_lists=_lookup_lists),
            NexusContextPattern(),
        ]

    def _annotate_context(
        self,
        annotation_tuples: list[tuple[docdeid.Token, docdeid.Token, str]],
        document: docdeid.Document,
    ) -> list[tuple[docdeid.Token, docdeid.Token, str]]:

        next_annotation_tuples = []

        for annotation_tuple in annotation_tuples:

            changes = False

            for context_pattern in self._context_patterns:
                res = context_pattern.apply(*annotation_tuple)

                if res is not None:
                    next_annotation_tuples.append(res)
                    changes = True
                    break

            if changes:
                continue
            else:
                next_annotation_tuples.append(annotation_tuple)

        # changes
        if set(annotation_tuples) != set(next_annotation_tuples):
            next_annotation_tuples = self._annotate_context(
                next_annotation_tuples, document
            )

        return next_annotation_tuples

    @staticmethod
    def get_context_tuples(document: docdeid.Document) -> list[tuple]:

        annotations = [
            annotation
            for annotation in document.annotations
            if deduce.utility.any_in_text(["initia", "naam", "interfix", "prefix"], annotation.tag)
        ]

        for annotation in annotations:
            document.remove_annotation(annotation)

        return [
            (annotation.start_token, annotation.end_token, annotation.tag)
            for annotation in annotations
        ]

    def annotate(self, document: docdeid.Document):

        annotation_tuples = self.get_context_tuples(document)
        annotation_tuples = self._annotate_context(annotation_tuples, document)

        annotations = set()

        @dataclass(frozen=True)
        class DeduceAnnotation(docdeid.Annotation):
            is_patient: bool = False

        # TODO: This needs a better implementation.
        for r in annotation_tuples:
            if r is not None:
                annotations.add(
                    DeduceAnnotation(
                        text=document.text[r[0].start_char : r[1].end_char],
                        start_char=r[0].start_char,
                        end_char=r[1].end_char,
                        tag="persoon",
                        is_patient="patient" in r[2],
                    )
                )

        ov = OverlapResolver(
            sort_by=["is_patient", "length"],
            sort_by_callbacks={"is_patient": lambda x: -x, "length": lambda x: -x},
        )

        annotations = ov.process(annotations, text=document.text)

        for annotation in annotations:
            document.add_annotation(
                docdeid.Annotation(
                    text=annotation.text,
                    start_char=annotation.start_char,
                    end_char=annotation.end_char,
                    tag="patient"
                    if getattr(annotation, "is_patient", False)
                    else "persoon",
                )
            )


def _get_name_pattern_annotators() -> dict[str, docdeid.BaseAnnotator]:

    annotators = {}

    for pattern_name, pattern in NAME_PATTERNS.items():
        annotators[pattern_name] = TokenPatternAnnotator(pattern=pattern)

    return annotators


def _get_regexp_annotators() -> dict[str, docdeid.BaseAnnotator]:

    annotators = {}

    for annotator_name, regexp_info in REGEPXS.items():
        annotators[annotator_name] = RegexpAnnotator(**regexp_info)

    return annotators


def get_annotators() -> dict[str, docdeid.BaseAnnotator]:

    annotators = _get_name_pattern_annotators()

    annotators |= {
        "institution": MultiTokenLookupAnnotator(
            lookup_values=_lookup_lists["institutions"],
            tokenizer=tokenizer,
            tag="instelling",
            string_processors=[LowercaseString()],
            merge=False,
        ),
        "residence": MultiTokenLookupAnnotator(
            lookup_values=_lookup_lists["residences"],
            tokenizer=tokenizer,
            tag="locatie",
            merge=False,
        ),
    }

    annotators |= _get_regexp_annotators()

    annotators |= {
        "name_context": NamesContextAnnotator(),
    }

    return annotators
