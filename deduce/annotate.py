""" The annotate module contains the code for annotating text"""
import re
from dataclasses import dataclass
from typing import Union, Optional, Any

from abc import ABC, abstractmethod

import itertools

import docdeid
from docdeid.annotation.annotation_processor import OverlapResolver
from docdeid.annotation.annotator import RegexpAnnotator, TrieAnnotator
from docdeid.datastructures.lookup import LookupList
from docdeid.string.processor import LowercaseString
from nltk.metrics import edit_distance

from deduce import utility
from deduce.lookup.lookup_lists import get_lookup_lists
from deduce.lookup.lookup_tries import get_lookup_tries
from deduce.tokenizer import Tokenizer


def _initialize():

    lookup_lists = get_lookup_lists()

    trie_merge_terms = LookupList()
    trie_merge_terms.add_items_from_iterable(["A1", "A2", "A3", "A4", "\n", "\r", "\t"])
    trie_merge_terms += lookup_lists["interfixes"]
    trie_merge_terms += lookup_lists["prefixes"]

    tokenizer = Tokenizer(merge_terms=trie_merge_terms)

    lookup_tries = get_lookup_tries(tokenizer)

    return lookup_lists, lookup_tries, tokenizer


_lookup_lists, _lookup_tries, tokenizer = _initialize()


@dataclass
class Person:
    first_names: list[str] = None
    initials: str = None
    surname: str = None
    given_name: str = None


class TokenContext:

    def __init__(self, position: int, tokens: list[docdeid.Token]):

        self._tokens = tokens
        self._position = position

    @property
    def token(self):
        return self._tokens[self._position]

    def next(self, num: int = 1):

        current_token = self._tokens[self._position]

        for _ in range(num):
            current_token = self._get_next_token(current_token.index)

            if current_token is None:
                return None

        return current_token

    def previous(self, num: int = 1):

        current_token = self._tokens[self._position]

        for _ in range(num):
            current_token = self.get_previous_token(current_token.index)

            if current_token is None:
                return None

        return current_token

    def num_tokens_from_position(self):

        return len(self._tokens) - self._position

    def get_token(self, pos: int):
        return self._tokens[pos]

    def get_token_at_num_from_position(self, num=0):
        return self._tokens[self._position + num]

    def _get_next_token(self, i: int) -> Union[docdeid.Token, None]:

        if i == len(self._tokens):
            return None

        for token in self._tokens[i + 1:]:

            if (
                    token.text[0] == ")"
                    or token.text[0] == ">"
                    or utility.any_in_text(["\n", "\r", "\t"], token.text)
            ):
                return None

            if token.text[0].isalpha():
                return token

        return None

    def get_previous_token(self, i: int) -> Union[docdeid.Token, None]:

        if i == 0:
            return None

        for token in self._tokens[i - 1:: -1]:

            if (
                    token.text[0] == "("
                    or token.text[0] == "<"
                    or utility.any_in_text(["\n", "\r", "\t"], token.text)
            ):
                return None

            if token.text[0].isalpha():
                return token

        return None

    @property
    def next_token(self):
        return self.next(1)

    @property
    def previous_token(self):
        return self.previous(1)


class TokenContextPattern(ABC):

    def __init__(self, tag: str):
        self._tag = tag

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:
        return True

    @abstractmethod
    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> Union[bool, tuple[bool, Any]]:
        pass

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:
        return token_context.token, token_context.token, self._tag

    def apply(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> Union[None, tuple]:

        if not self.precondition(token_context, meta_data):
            return None

        match = self.match(token_context, meta_data)
        match_info = None

        if isinstance(match, tuple):
            match, match_info = match  # unpack

        if match:
            return self.annotate(token_context, match_info)


class PrefixWithNamePattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return token_context.next_token is not None

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token_context.token.text.lower() in _lookup_lists["prefixes"],
                token_context.next_token.text[0].isupper(),
                token_context.next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.next_token, self._tag


class InterfixWithNamePattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:
        return token_context.next_token is not None

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token_context.token.text.lower() in _lookup_lists["interfixes"],
                token_context.next_token.text in _lookup_lists["interfix_surnames"],
                token_context.next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.next_token, self._tag


class InitialWithCapitalPattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return token_context.next_token is not None

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token_context.token.text[0].isupper(),
                len(token_context.token.text) == 1,

                len(token_context.next_token.text) > 3,
                token_context.next_token.text[0].isupper(),
                token_context.next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.next_token, self._tag


class InitiaalInterfixCapitalPattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token_context.previous_token is not None,
                token_context.next_token is not None,
            ]
        )

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token_context.previous_token.text[0].isupper(),
                len(token_context.previous_token.text) == 1,

                token_context.token.text in _lookup_lists["interfixes"],

                token_context.next_token.text[0].isupper(),
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.previous_token, token_context.next_token, self._tag


class FirstNameLookupPattern(TokenContextPattern):

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                token_context.token.text in _lookup_lists["first_names"],
                token_context.token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.token, self._tag


class SurnameLookupPattern(TokenContextPattern):

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:
        return all(
            [
                token_context.token.text in _lookup_lists["surnames"],
                token_context.token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:
        return token_context.token, token_context.token, self._tag


class PersonFirstNamePattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                meta_data is not None,
                'person' in meta_data,
                meta_data['person'].first_names is not None
            ]
        )

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data['person'].first_names):

            condition = token_context.token.text == first_name or \
                all(
                    [
                        len(token_context.token.text) > 3,
                        edit_distance(token_context.token.text, first_name, transpositions=True) <= 1
                    ]
                )

            if condition:
                return True, token_context.token.index

        return False

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return (
            token_context.get_token(pos=match_info),
            token_context.get_token(pos=match_info),
            self._tag
        )


class PersonInitialFromNamePattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                meta_data is not None,
                'person' in meta_data,
                meta_data['person'].first_names is not None
            ]
        )

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> Union[bool, tuple[bool, Any]]:

        for i, first_name in enumerate(meta_data['person'].first_names):

            if token_context.token.text == first_name[0]:

                next_token = token_context.next(1)
                if (next_token is not None) and next_token == ".":
                    return True, (token_context.token.index, next_token.index)

                return True, (token_context.token.index, token_context.token.index)

        return False

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return (
            token_context.get_token(pos=match_info[0]),
            token_context.get_token(pos=match_info[1]),
            self._tag
        )


class PersonSurnamePattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                meta_data is not None,
                'person' in meta_data,
                meta_data['person'].surname is not None
            ]
        )

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> Union[bool, tuple[bool, Any]]:

        surname_pattern = [token.text for token in tokenizer.tokenize(meta_data['patient_surname'])]

        if len(surname_pattern) > token_context.num_tokens_from_position():
            return False

        return all(
                [
                    edit_distance(surname_token, token_context.get_token_at_num_from_position(i).text, transpositions=True) <= 1
                    for surname_token, i in zip(surname_pattern, itertools.count())
                ]
            ), len(surname_pattern)-1

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return (
            token_context.get_token_at_num_from_position(0),
            token_context.get_token_at_num_from_position(match_info),
            self._tag,
        )


class PersonInitialsPattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                meta_data is not None,
                'person' in meta_data,
                meta_data['person'].initials is not None
            ]
        )

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return token_context.token.text == meta_data['person'].initials

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.token, self._tag


class PersonGivenNamePattern(TokenContextPattern):

    def precondition(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return all(
            [
                meta_data is not None,
                'person' in meta_data,
                meta_data['person'].given_name is not None
            ]
        )

    def match(self, token_context: TokenContext, meta_data: Optional[dict] = None) -> bool:

        return (token_context.token.text == meta_data['person'].given_name) or \
               all(
                   [
                       len(token_context.token.text) > 3,
                       edit_distance(token_context.token.text, meta_data['person'].given_name, transpositions=True) <= 1,
                   ]
               )

    def annotate(self, token_context: TokenContext, match_info=None) -> tuple:

        return token_context.token, token_context.token, self._tag


class NamesAnnotator(docdeid.BaseAnnotator):

    def __init__(self):

        self._patterns = [
            PrefixWithNamePattern(tag="prefix+naam"),
            InterfixWithNamePattern(tag="interfix+naam"),
            InitialWithCapitalPattern(tag="initiaal+naam"),
            InitiaalInterfixCapitalPattern(tag="initiaal+interfix+naam"),
            FirstNameLookupPattern(tag="voornaam_onbekend"),
            SurnameLookupPattern(tag="achternaam_onbekend"),
            PersonFirstNamePattern(tag="voornaam_patient"),
            PersonInitialFromNamePattern(tag="initiaal_patient"),
            PersonInitialsPattern(tag="initialen_patient"),
            PersonGivenNamePattern(tag="roepnaam_patient"),
            PersonSurnamePattern(tag="achternaam_patient")
        ]

    @staticmethod
    def _parse_str_field(i: str) -> Union[None, str]:
        """ Maps None or empty string to None, else to string itself. """
        return i or None

    def _parse_person_data(self, meta_data: dict) -> Person:

        first_names = self._parse_str_field(meta_data.get('patient_first_names', None))

        if first_names is not None:
            first_names = first_names.split(" ")

        initials = self._parse_str_field(meta_data.get('patient_initials', None))
        surname = self._parse_str_field(meta_data.get('patient_surname', None))
        given_name = self._parse_str_field(meta_data.get('patient_given_name', None))

        return Person(first_names, initials, surname, given_name)

    def annotate_raw(self, document: docdeid.Document):

        person = self._parse_person_data(document.get_meta_data())
        document.add_meta_data_item('person', person)

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
                utility.any_in_text(
                    ["initia", "voornaam", "roepnaam", "prefix"], tag
                ),
                len(next_token.text) > 3,
                next_token.text[0].isupper(),
                next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        if condition:
            return start_token, next_token, f"{tag}+initiaalhoofdletternaam"  # TODO drop initiaal here

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
                    r = self._match_nexus(
                        tag, start_token, next_token, next_next_token
                    )

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


class InstitutionAnnotator(TrieAnnotator):
    def __init__(self):
        super().__init__(
            trie=_lookup_tries["institutions"],
            tag="instelling",
            string_processors=[LowercaseString()],
        )


class AltrechtAnnotator(RegexpAnnotator):
    def __init__(self):

        altrecht_pattern = re.compile(
            r"[aA][lL][tT][rR][eE][cC][hH][tT]((\s[A-Z][\w]*)*)"
        )

        super().__init__(regexp_patterns=[altrecht_pattern], tag="instelling")


class ResidenceAnnotator(TrieAnnotator):
    def __init__(self):
        super().__init__(trie=_lookup_tries["residences"], tag="locatie")


class AddressAnnotator(RegexpAnnotator):
    def __init__(self):

        address_pattern = re.compile(
            r"([A-Z]\w+(baan|bolwerk|dam|dijk|dreef|gracht|hof|kade|laan|markt|pad|park|"
            r"plantsoen|plein|singel|steeg|straat|weg)(\s(\d+){1,6}\w{0,2})?)(\W|$)"
        )

        super().__init__(
            regexp_patterns=[address_pattern], tag="locatie", capturing_group=1
        )


class PostalcodeAnnotator(RegexpAnnotator):
    def __init__(self):

        date_pattern = re.compile(
            r"(\d{4} (?!MG)[A-Z]{2}|\d{4}(?!mg|MG)[a-zA-Z]{2})(\W|$)"
        )

        super().__init__(
            regexp_patterns=[date_pattern], tag="locatie", capturing_group=1
        )


class PostbusAnnotator(RegexpAnnotator):
    def __init__(self):

        postbus_pattern = re.compile(r"([Pp]ostbus\s\d{5})")

        super().__init__(
            regexp_patterns=[postbus_pattern],
            tag="locatie",
        )


class PhoneNumberAnnotator(RegexpAnnotator):
    def __init__(self):

        phone_pattern_1 = re.compile(
            r"(((0)[1-9]{2}[0-9][-]?[1-9][0-9]{5})|((\+31|0|0031)[1-9][0-9][-]?[1-9][0-9]{6}))"
        )

        phone_pattern_2 = re.compile(r"(((\+31|0|0031)6)[-]?[1-9][0-9]{7})")

        phone_pattern_3 = re.compile(r"((\(\d{3}\)|\d{3})\s?\d{3}\s?\d{2}\s?\d{2})")

        super().__init__(
            regexp_patterns=[phone_pattern_1, phone_pattern_2, phone_pattern_3],
            tag="telefoonnummer",
        )


class PatientNumberAnnotator(RegexpAnnotator):
    def __init__(self):

        patientnumber_pattern = re.compile(r"\d{7}")

        super().__init__(
            regexp_patterns=[patientnumber_pattern], tag="patientnummer"
        )


class DateAnnotator(RegexpAnnotator):
    def __init__(self):

        date_pattern_1 = re.compile(
            r"(([1-9]|0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012]|[1-9])([- /.]{,2}(\d{4}|\d{2}))?)(\D|$)"
        )

        date_pattern_2 = re.compile(
            r"(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|"
            r"november|december)([- /.]{,2}(\d{4}|\d{2}))?)(\D|$)"
        )

        super().__init__(
            regexp_patterns=[date_pattern_1, date_pattern_2],
            tag="datum",
            capturing_group=1,
        )


class AgeAnnotator(RegexpAnnotator):
    def __init__(self):

        age_pattern = re.compile(r"(\d{1,3})([ -](jarige|jarig|jaar))")

        super().__init__(
            regexp_patterns=[age_pattern], tag="leeftijd", capturing_group=1
        )


class UrlAnnotator(RegexpAnnotator):
    def __init__(self):

        url_pattern_1 = re.compile(
            r"((?!mailto:)"
            r"((?:http|https|ftp)://)"
            r"(?:\S+(?::\S*)?@)?(?:(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
            r"(\.(?:[0-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|((?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)"
            r"(?:\.(?:[a-z\u00a1-\uffff0-9]+-?)*[a-z\u00a1-\uffff0-9]+)*(\.([a-z\u00a1-\uffff]{2,})))|localhost)"
            r"(?::\d{2,5})?(?:([/?#])[^\s]*)?)"
        )

        url_pattern_2 = re.compile(r"([\w\d.-]{3,}(\.)(nl|com|net|be)(/[^\s]+)?)")

        super().__init__(regexp_patterns=[url_pattern_1, url_pattern_2], tag="url")


class EmailAnnotator(RegexpAnnotator):
    def __init__(self):

        email_pattern = re.compile(
            r"([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)"
        )

        super().__init__(regexp_patterns=[email_pattern], tag="url")
