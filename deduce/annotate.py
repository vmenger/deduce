""" The annotate module contains the code for annotating text"""
import re
from dataclasses import dataclass
from typing import Union

import docdeid
from deduce import utility
from deduce.lookup.lookup_lists import get_lookup_lists
from deduce.name_patterns import (
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
from deduce.tokenizer import TokenContext, Tokenizer
from docdeid.annotate.annotation_processor import OverlapResolver
from docdeid.annotate.annotator import MultiTokenLookupAnnotator, RegexpAnnotator
from docdeid.ds.lookup import LookupList
from docdeid.str.processor import LowercaseString


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


class NamesAnnotator(docdeid.BaseAnnotator):
    def __init__(self):

        self._patterns = [
            PrefixWithNamePattern(tag="prefix+naam", lookup_lists=_lookup_lists),
            InterfixWithNamePattern(tag="interfix+naam", lookup_lists=_lookup_lists),
            InitialWithCapitalPattern(tag="initiaal+naam", lookup_lists=_lookup_lists),
            InitiaalInterfixCapitalPattern(
                tag="initiaal+interfix+naam", lookup_lists=_lookup_lists
            ),
            FirstNameLookupPattern(tag="voornaam_onbekend", lookup_lists=_lookup_lists),
            SurnameLookupPattern(tag="achternaam_onbekend", lookup_lists=_lookup_lists),
            PersonFirstNamePattern(tag="voornaam_patient"),
            PersonInitialFromNamePattern(tag="initiaal_patient"),
            PersonInitialsPattern(tag="initialen_patient"),
            PersonGivenNamePattern(tag="roepnaam_patient"),
            PersonSurnamePattern(tag="achternaam_patient", tokenizer=tokenizer),
        ]

    @staticmethod
    def _parse_str_field(i: str) -> Union[None, str]:
        """Maps None or empty string to None, else to string itself."""
        return i or None

    def _parse_person_data(self, meta_data: dict) -> Person:

        first_names = self._parse_str_field(meta_data.get("patient_first_names", None))

        if first_names is not None:
            first_names = first_names.split(" ")

        initials = self._parse_str_field(meta_data.get("patient_initials", None))
        surname = self._parse_str_field(meta_data.get("patient_surname", None))
        given_name = self._parse_str_field(meta_data.get("patient_given_name", None))

        return Person(first_names, initials, surname, given_name)

    def annotate_raw(self, document: docdeid.Document):

        person = self._parse_person_data(document.get_meta_data())
        document.add_meta_data_item("person", person)

        tokens = document.tokens
        annotation_tuples = []

        for i, token in enumerate(tokens):

            token_context = TokenContext(position=i, tokens=tokens)

            for pattern in self._patterns:
                tup = pattern.apply(token_context, document.get_meta_data())
                annotation_tuples.append(tup)

        return annotation_tuples

    @staticmethod
    def _match_initials_context(previous_token, tag, end_token):

        previous_token_is_initial = all(
            [len(previous_token.text) == 1, previous_token.text[0].isupper()]
        )

        previous_token_is_name = all(
            [
                previous_token.text != "",
                previous_token.text[0].isupper(),
                previous_token.text.lower() not in _lookup_lists["whitelist"],
                previous_token.text.lower() not in _lookup_lists["prefixes"],
            ]
        )

        initial_condition = all(
            [
                utility.any_in_text(["achternaam", "interfix", "initia"], tag),
                any([previous_token_is_initial, previous_token_is_name]),
            ]
        )

        if initial_condition:
            return previous_token, end_token, f"initiaal+{tag}"

    @staticmethod
    def _match_interfix_context(tag, start_token, next_token, next_next_token):

        condition = all(
            [
                utility.any_in_text(["initia", "naam"], tag),
                next_token.text in _lookup_lists["interfixes"],
                next_next_token.text[0].isupper(),
            ]
        )

        if condition:
            return start_token, next_next_token, f"{tag}+interfix+achternaam"

    @staticmethod
    def _match_initial_name_context(tag, start_token, next_token):

        condition = all(
            [
                utility.any_in_text(["initia", "voornaam", "roepnaam", "prefix"], tag),
                len(next_token.text) > 3,
                next_token.text[0].isupper(),
                next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        if condition:
            return (
                start_token,
                next_token,
                f"{tag}+initiaalhoofdletternaam",
            )  # TODO drop initiaal here

    @staticmethod
    def _match_nexus(tag, start_token, next_token, next_next_token):

        condition = all([next_token.text == "en", next_next_token.text[0].isupper()])

        if condition:
            return start_token, next_next_token, f"{tag}+en+hoofdletternaam"

    def annotate_context(
        self,
        annotation_tuples: list[tuple[docdeid.Token, docdeid.Token, str]],
        document: docdeid.Document,
    ) -> list[tuple[docdeid.Token, docdeid.Token, str]]:

        # print(annotation_tuples)

        tokens = document.tokens
        next_annotation_tuples = []
        changes = False

        for start_token, end_token, tag in annotation_tuples:

            previous_token = TokenContext(start_token.index, tokens).previous(1)
            next_token = TokenContext(end_token.index, tokens).next(1)

            if previous_token is not None:

                # 1
                r = self._match_initials_context(previous_token, tag, end_token)

                if r is not None:
                    next_annotation_tuples.append(r)
                    changes = True
                    continue

            if next_token is not None:

                next_next_token = TokenContext(next_token.index, tokens).next()

                if next_next_token is not None:

                    # 2
                    r = self._match_interfix_context(
                        tag, start_token, next_token, next_next_token
                    )

                    if r is not None:
                        next_annotation_tuples.append(r)
                        changes = True
                        continue

                # 3
                r = self._match_initial_name_context(tag, start_token, next_token)

                if r is not None:
                    next_annotation_tuples.append(r)
                    changes = True
                    continue

                if next_next_token is not None:

                    # 4
                    r = self._match_nexus(tag, start_token, next_token, next_next_token)

                    if r is not None:
                        next_annotation_tuples.append(r)
                        changes = True
                        continue

            next_annotation_tuples.append((start_token, end_token, tag))

        if changes:
            next_annotation_tuples = self.annotate_context(
                next_annotation_tuples, document
            )

        return next_annotation_tuples

    def annotate(self, document: docdeid.Document):

        annotation_tuples = self.annotate_raw(document)

        annotation_tuples = [a for a in annotation_tuples if a is not None]
        annotation_tuples = self.annotate_context(annotation_tuples, document)

        annotations = set()

        @dataclass(frozen=True)
        class DeduceAnnotation(docdeid.Annotation):
            is_patient: bool

        # TODO: This needs implementation.
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


def _get_regexp_annotators() -> dict[str, docdeid.BaseAnnotator]:

    annotators = {}

    for annotator_name, regexp_info in REGEPXS.items():
        annotators[annotator_name] = RegexpAnnotator(**regexp_info)

    return annotators


def get_annotators() -> dict[str, docdeid.BaseAnnotator]:

    annotators = {
        "name": NamesAnnotator(),
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

    return annotators
