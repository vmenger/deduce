""" The annotate module contains the code for annotating text"""

import re
from typing import Union

import docdeid
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


class NamesAnnotator(docdeid.BaseAnnotator):
    @staticmethod
    def _match_prefix(
        token: docdeid.Token, next_token: docdeid.Token
    ) -> tuple[docdeid.Token, docdeid.Token, str]:

        condition = all(
            [
                token.text.lower() in _lookup_lists["prefixes"],
                next_token.text[0].isupper(),
                next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        if condition:
            return token, next_token, "PREFIXNAAM"

    @staticmethod
    def _match_interfix(
        token: docdeid.Token, next_token: docdeid.Token
    ) -> tuple[docdeid.Token, docdeid.Token, str]:

        condition = all(
            [
                token.text.lower() in _lookup_lists["interfixes"],
                next_token.text in _lookup_lists["interfix_surnames"],
                next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        if condition:
            return token, next_token, "INTERFIXNAAM"

    def _match_initial_with_capital(
        self, token: docdeid.Token, next_token: docdeid.Token
    ) -> tuple[docdeid.Token, docdeid.Token, str]:

        condition = all(
            [
                token.text[0].isupper(),
                len(token.text) == 1,
                len(next_token.text) > 3,
                next_token.text[0].isupper(),
                next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        if condition:

            return token, next_token, "INITIAALHOOFDLETTERNAAM"

    def _match_interfix_with_initial(
        self,
        token: docdeid.Token,
        next_token: docdeid.Token,
        previous_token: docdeid.Token,
    ) -> tuple[docdeid.Token, docdeid.Token, str]:

        condition = all(
            [
                previous_token.text[0].isupper(),
                len(previous_token.text) == 1,
                token.text in _lookup_lists["interfixes"],
                next_token.text[0].isupper(),
            ]
        )

        if condition:
            return previous_token, next_token, "INITIAALINTERFIXNAAM"

    @staticmethod
    def _match_first_names(
        token: docdeid.Token, next_token: docdeid.Token, patient_first_names: list[str]
    ) -> tuple[docdeid.Token, docdeid.Token, str]:

        for patient_first_name in patient_first_names:

            # Check if the initial matches
            if token.text == patient_first_name[0]:

                # If followed by a period, also annotate the period
                if (next_token is not None) and next_token.text == ".":
                    return token, next_token, "INITIAALPAT"
                else:
                    return token, token, "INITIAALPAT"

            # Check if full name matches
            condition = any(
                [
                    token.text == patient_first_name,
                    all(
                        [
                            len(token.text) > 3,
                            edit_distance(
                                token.text, patient_first_name, transpositions=True
                            )
                            <= 1,
                        ]
                    ),
                ]
            )

            if condition:
                return token, token, "VOORNAAMPAT"

    @staticmethod
    def _match_initials(
        token: docdeid.Token, patient_initials: str
    ) -> Union[tuple[docdeid.Token, docdeid.Token, str], None]:

        if token.text == patient_initials:
            return token, token, "INITIALENPAT"

    @staticmethod
    def _match_surnames(
        tokens: list[docdeid.Token], patient_surname: str
    ) -> Union[tuple[docdeid.Token, docdeid.Token, str], None]:

        surname_pattern = [token.text for token in tokenizer.tokenize(patient_surname)]

        if len(surname_pattern) > len(tokens):
            return None

        condition = all(
            [
                edit_distance(token.text, surname_token, transpositions=True) <= 1
                for token, surname_token in zip(tokens, surname_pattern)
            ]
        )

        if condition:
            return (
                tokens[0],
                tokens[len(surname_pattern) - 1],
                "ACHTERNAAMPAT",
            )

    @staticmethod
    def _match_given_name(
        token: docdeid.Token, patient_given_name: str
    ) -> Union[tuple[docdeid.Token, docdeid.Token, str], None]:

        # Check if full name matches
        condition = any(
            [
                token.text == patient_given_name,
                all(
                    [
                        len(token.text) > 3,
                        edit_distance(
                            token.text, patient_given_name, transpositions=True
                        )
                        <= 1,
                    ]
                ),
            ]
        )

        if condition:
            return token, token, "ROEPNAAMPAT"

    @staticmethod
    def _match_lookup_name(
        token: docdeid.Token,
    ) -> Union[tuple[docdeid.Token, docdeid.Token, str], None]:

        first_name_condition = all(
            [
                token.text in _lookup_lists["first_names"],
                token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        last_name_condition = all(
            [
                token.text in _lookup_lists["surnames"],
                token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        if first_name_condition:
            return token, token, "VOORNAAMONBEKEND"

        if last_name_condition:
            return token, token, "ACHTERNAAMONBEKEND"

        return None

    @staticmethod
    def _parse_first_names(document: docdeid.Document) -> Union[list[str], None]:

        patient_first_names = document.get_meta_data_item("patient_first_names")

        if patient_first_names is None or patient_first_names == "":
            return None

        return patient_first_names.split(" ")

    @staticmethod
    def _parse_initials(document: docdeid.Document) -> Union[str, None]:

        patient_initials = document.get_meta_data_item("patient_initials")

        if patient_initials is None or patient_initials == "":
            return None

        return patient_initials

    @staticmethod
    def _parse_surname(document: docdeid.Document) -> Union[str, None]:

        patient_surname = document.get_meta_data_item("patient_surname")

        if patient_surname is None or patient_surname == "":
            return None

        return patient_surname

    @staticmethod
    def _parse_given_name(document: docdeid.Document) -> Union[str, None]:

        patient_given_name = document.get_meta_data_item("patient_given_name")

        if patient_given_name is None or patient_given_name == "":
            return None

        return patient_given_name

    def annotate_raw(self, document: docdeid.Document):

        patient_first_names = self._parse_first_names(document)
        patient_initials = self._parse_initials(document)
        patient_surname = self._parse_surname(document)
        patient_given_name = self._parse_given_name(document)

        tokens = document.tokens

        annotation_tuples = []

        for i, token in enumerate(tokens):

            next_token = utility.get_next_token(tokens, i)
            previous_token = utility.get_previous_token(tokens, i)

            if next_token is not None:

                annotation_tuples.append(self._match_prefix(token, next_token))
                annotation_tuples.append(self._match_interfix(token, next_token))
                annotation_tuples.append(
                    self._match_initial_with_capital(token, next_token)
                )

                if previous_token is not None:
                    annotation_tuples.append(
                        self._match_interfix_with_initial(
                            token, next_token, previous_token
                        )
                    )

            if patient_first_names is not None:
                annotation_tuples.append(
                    self._match_first_names(token, next_token, patient_first_names)
                )

            if patient_initials is not None:
                annotation_tuples.append(self._match_initials(token, patient_initials))

            if patient_surname is not None:
                annotation_tuples.append(
                    self._match_surnames(tokens[i:], patient_surname)
                )

            if patient_given_name is not None:
                annotation_tuples.append(
                    self._match_given_name(token, patient_given_name)
                )

            annotation_tuples.append(self._match_lookup_name(token))

        return annotation_tuples

    def _match_initials_context(self, previous_token, category, end_token):

        previous_token_is_initial = all(
            [len(previous_token.text) == 1, previous_token.text[0].isupper()]
        )

        previous_token_is_name = all(
            [
                previous_token.text != "",
                previous_token.text[0].isupper(),
                previous_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        initial_condition = all(
            [
                utility.any_in_text(["ACHTERNAAM", "INTERFIX", "INITIAAL"], category),
                any([previous_token_is_initial, previous_token_is_name]),
            ]
        )

        if initial_condition:
            return previous_token, end_token, f"INITIAAL|{category}"

    def _match_interfix_context(
        self, category, start_token, next_token, next_next_token
    ):

        condition = all(
            [
                utility.any_in_text(["INITI", "NAAM"], category),
                next_token.text in _lookup_lists["interfixes"],
                next_next_token.text[0].isupper(),
            ]
        )

        if condition:
            return start_token, next_next_token, f"{category}|INTERFIXACHTERNAAM"

    def _match_initial_name_context(self, category, start_token, next_token):

        condition = all(
            [
                utility.any_in_text(
                    ["INITI", "VOORNAAM", "ROEPNAAM", "PREFIX"], category
                ),
                len(next_token.text) > 3,
                next_token.text[0].isupper(),
                next_token.text.lower() not in _lookup_lists["whitelist"],
            ]
        )

        if condition:
            return start_token, next_token, f"{category}|INITIAALHOOFDLETTERNAAM"

    def _match_nexus(self, category, start_token, next_token, next_next_token):

        condition = all([next_token.text == "en", next_next_token.text[0].isupper()])

        if condition:
            return start_token, next_next_token, f"{category}|MEERDERPERSONEN"

    def annotate_context(
        self,
        annotation_tuples: list[tuple[docdeid.Token, docdeid.Token, str]],
        document: docdeid.Document,
    ) -> list[tuple[docdeid.Token, docdeid.Token, str]]:

        print(annotation_tuples)

        tokens = document.tokens
        next_annotation_tuples = []
        changes = False

        for start_token, end_token, category in annotation_tuples:

            previous_token = utility.get_previous_token(tokens, start_token.index)
            next_token = utility.get_next_token(tokens, end_token.index)

            if previous_token is not None:

                # 1
                r = self._match_initials_context(previous_token, category, end_token)

                if r is not None:
                    next_annotation_tuples.append(r)
                    changes = True
                    continue

            if next_token is not None:

                next_next_token = utility.get_next_token(tokens, next_token.index)

                if next_next_token is not None:

                    # 2
                    r = self._match_interfix_context(
                        category, start_token, next_token, next_next_token
                    )

                    if r is not None:
                        next_annotation_tuples.append(r)
                        changes = True
                        continue

                # 3
                r = self._match_initial_name_context(category, start_token, next_token)

                if r is not None:
                    next_annotation_tuples.append(r)
                    changes = True
                    continue

                if next_next_token is not None:

                    # 4
                    r = self._match_nexus(
                        category, start_token, next_token, next_next_token
                    )

                    if r is not None:
                        next_annotation_tuples.append(r)
                        changes = True
                        continue

            next_annotation_tuples.append((start_token, end_token, category))

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

        from dataclasses import dataclass

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
                        category="PERSOON",
                        is_patient="PAT" in r[2],
                    )
                )

        from docdeid.annotation.annotation_processor import OverlapResolver

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
                    category="PATIENT"
                    if getattr(annotation, "is_patient", False)
                    else "PERSOON",
                )
            )


class InstitutionAnnotator(TrieAnnotator):
    def __init__(self):
        super().__init__(
            trie=_lookup_tries["institutions"],
            category="INSTELLING",
            string_processors=[LowercaseString()],
        )


class AltrechtAnnotator(RegexpAnnotator):
    def __init__(self):

        altrecht_pattern = re.compile(
            r"[aA][lL][tT][rR][eE][cC][hH][tT]((\s[A-Z][\w]*)*)"
        )

        super().__init__(regexp_patterns=[altrecht_pattern], category="INSTELLING")


class ResidenceAnnotator(TrieAnnotator):
    def __init__(self):
        super().__init__(trie=_lookup_tries["residences"], category="LOCATIE")


class AddressAnnotator(RegexpAnnotator):
    def __init__(self):

        address_pattern = re.compile(
            r"([A-Z]\w+(baan|bolwerk|dam|dijk|dreef|gracht|hof|kade|laan|markt|pad|park|"
            r"plantsoen|plein|singel|steeg|straat|weg)(\s(\d+){1,6}\w{0,2})?)(\W|$)"
        )

        super().__init__(
            regexp_patterns=[address_pattern], category="LOCATIE", capturing_group=1
        )


class PostalcodeAnnotator(RegexpAnnotator):
    def __init__(self):

        date_pattern = re.compile(
            r"(\d{4} (?!MG)[A-Z]{2}|\d{4}(?!mg|MG)[a-zA-Z]{2})(\W|$)"
        )

        super().__init__(
            regexp_patterns=[date_pattern], category="LOCATIE", capturing_group=1
        )


class PostbusAnnotator(RegexpAnnotator):
    def __init__(self):

        postbus_pattern = re.compile(r"([Pp]ostbus\s\d{5})")

        super().__init__(
            regexp_patterns=[postbus_pattern],
            category="LOCATIE",
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
            category="TELEFOONNUMMER",
        )


class PatientNumberAnnotator(RegexpAnnotator):
    def __init__(self):

        patientnumber_pattern = re.compile(r"\d{7}")

        super().__init__(
            regexp_patterns=[patientnumber_pattern], category="PATIENTNUMMER"
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
            category="DATUM",
            capturing_group=1,
        )


class AgeAnnotator(RegexpAnnotator):
    def __init__(self):

        age_pattern = re.compile(r"(\d{1,3})([ -](jarige|jarig|jaar))")

        super().__init__(
            regexp_patterns=[age_pattern], category="LEEFTIJD", capturing_group=1
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

        super().__init__(regexp_patterns=[url_pattern_1, url_pattern_2], category="URL")


class EmailAnnotator(RegexpAnnotator):
    def __init__(self):

        email_pattern = re.compile(
            r"([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)"
        )

        super().__init__(regexp_patterns=[email_pattern], category="URL")
