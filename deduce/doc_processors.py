import re
from collections import OrderedDict

import docdeid as dd

from deduce.annotate.annotation_processing import PersonAnnotationConverter
from deduce.annotate.annotator import AnnotationContextPatternAnnotator
from deduce.pattern.name import (
    FirstNameLookupPattern,
    InitiaalInterfixCapitalPattern,
    InitialWithCapitalPattern,
    InterfixWithNamePattern,
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
from deduce.pattern.name_patient import (
    PersonFirstNamePattern,
    PersonInitialFromNamePattern,
    PersonInitialsPattern,
    PersonSurnamePattern,
)
from deduce.tokenize.tokenizer import DeduceTokenizer

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


def _get_name_pattern_annotators(
    lookup_sets: dd.ds.DsCollection, tokenizer: dd.BaseTokenizer
) -> OrderedDict[str, dd.doc.DocProcessor]:

    name_patterns = {
        "prefix_with_name": PrefixWithNamePattern(tag="prefix+naam", lookup_sets=lookup_sets),
        "interfix_with_name": InterfixWithNamePattern(tag="interfix+naam", lookup_sets=lookup_sets),
        "initial_with_capital": InitialWithCapitalPattern(tag="initiaal+naam", lookup_sets=lookup_sets),
        "initial_interfix": InitiaalInterfixCapitalPattern(tag="initiaal+interfix+naam", lookup_sets=lookup_sets),
        "first_name_lookup": FirstNameLookupPattern(tag="voornaam_onbekend", lookup_sets=lookup_sets),
        "surname_lookup": SurnameLookupPattern(tag="achternaam_onbekend", lookup_sets=lookup_sets),
        "person_first_name": PersonFirstNamePattern(tag="voornaam_patient"),
        "person_initial_from_name": PersonInitialFromNamePattern(tag="initiaal_patient"),
        "person_initials": PersonInitialsPattern(tag="initialen_patient"),
        "person_surname": PersonSurnamePattern(tag="achternaam_patient", tokenizer=tokenizer),
    }

    annotators = OrderedDict()

    for pattern_name, pattern in name_patterns.items():
        annotators[pattern_name] = dd.annotate.TokenPatternAnnotator(pattern=pattern)

    return annotators


def _get_name_context_patterns(lookup_sets: dd.ds.DsCollection) -> list[AnnotationContextPattern]:

    return [
        InitialsContextPattern(tag="initiaal+{tag}", lookup_sets=lookup_sets),
        InterfixContextPattern(tag="{tag}+interfix+achternaam", lookup_sets=lookup_sets),
        InitialNameContextPattern(tag="{tag}+initiaalhoofdletternaam", lookup_sets=lookup_sets),
        NexusContextPattern(tag="{tag}+en+hoofdletternaam"),
    ]


def _get_regexp_annotators() -> OrderedDict[str, dd.doc.DocProcessor]:

    annotators = OrderedDict()

    for annotator_name, regexp_info in REGEPXS.items():
        annotators[annotator_name] = dd.annotate.RegexpAnnotator(**regexp_info)

    return annotators


def _get_name_processor_group(lookup_sets: dd.ds.DsCollection, tokenizer: dd.BaseTokenizer) -> dd.doc.DocProcessorGroup:

    name_processors = _get_name_pattern_annotators(lookup_sets, tokenizer)

    name_processors["name_context"] = AnnotationContextPatternAnnotator(
        context_patterns=_get_name_context_patterns(lookup_sets), tags=["initia", "naam", "interfix", "prefix"]
    )

    name_processors["person_annotation_converter"] = PersonAnnotationConverter()

    return dd.doc.DocProcessorGroup(name_processors)


def get_doc_processors(
    lookup_sets: dd.ds.DsCollection[dd.LookupSet], tokenizer: dd.BaseTokenizer
) -> OrderedDict[str, dd.doc.DocProcessor]:

    annotators = OrderedDict()

    annotators["name_group"] = _get_name_processor_group(lookup_sets, tokenizer)

    annotators["institution"] = dd.annotate.MultiTokenLookupAnnotator(
        lookup_values=lookup_sets["institutions"],
        tokenizer=DeduceTokenizer(),
        tag="instelling",
        matching_pipeline=lookup_sets["institutions"].matching_pipeline,
    )

    annotators["residence"] = dd.annotate.MultiTokenLookupAnnotator(
        lookup_values=lookup_sets["residences"],
        tokenizer=DeduceTokenizer(),
        tag="locatie",
    )

    annotators |= _get_regexp_annotators()

    return annotators
