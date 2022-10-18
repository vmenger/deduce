from typing import Optional

import docdeid as dd

from deduce.utils import str_match


class PersonFirstNamePattern(dd.pattern.TokenPattern):
    def doc_precondition(self, doc: dd.Document) -> bool:

        patient = doc.get_metadata_item("patient")
        return (patient is not None) and (patient.first_names is not None)

    def match(self, token: dd.Token, metadata: Optional[dict] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        for first_name in metadata["patient"].first_names:

            if str_match(token.text, first_name) or (
                len(token.text) > 3 and str_match(token.text, first_name, max_edit_distance=1)
            ):

                return token, token

        return None


class PersonInitialFromNamePattern(dd.pattern.TokenPattern):
    def doc_precondition(self, doc: dd.Document) -> bool:

        patient = doc.get_metadata_item("patient")
        return (patient is not None) and (patient.first_names is not None)

    def match(self, token: dd.Token, metadata: Optional[dict] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        for _, first_name in enumerate(metadata["patient"].first_names):

            if str_match(token.text, first_name[0]):

                next_token = token.next()

                if (next_token is not None) and str_match(next_token.text, "."):
                    return token, next_token

                return token, token

        return None


class PersonInitialsPattern(dd.pattern.TokenPattern):
    def doc_precondition(self, doc: dd.Document) -> bool:

        patient = doc.get_metadata_item("patient")
        return (patient is not None) and (patient.initials is not None)

    def match(self, token: dd.Token, metadata: Optional[dict] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        if str_match(token.text, metadata["patient"].initials):
            return token, token

        return None


class PersonSurnamePattern(dd.pattern.TokenPattern):
    def __init__(self, tokenizer: dd.BaseTokenizer, *args, **kwargs) -> None:
        self._tokenizer = tokenizer
        super().__init__(*args, **kwargs)

    def doc_precondition(self, doc: dd.Document) -> bool:

        patient = doc.metadata["patient"]

        if (patient is None) or (patient.surname is None):
            return False

        doc.metadata["surname_pattern"] = self._tokenizer.tokenize(patient.surname)

        return True

    def match(self, token: dd.Token, metadata: Optional[dict] = None) -> Optional[tuple[dd.Token, dd.Token]]:

        surname_pattern = metadata["surname_pattern"]
        surname_token = surname_pattern[0]
        start_token = token

        while True:

            if not str_match(surname_token.text, token.text, max_edit_distance=1):
                return None

            match_end_token = token

            surname_token = surname_token.next()
            token = token.next()

            if surname_token is None:
                return start_token, match_end_token  # end of pattern

            if token is None:
                return None  # end of tokens