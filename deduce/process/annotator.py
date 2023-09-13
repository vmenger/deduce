import re
from typing import Optional

import docdeid as dd
from docdeid import Annotation, Document

import deduce.utils


class TokenPatternAnnotator(dd.process.Annotator):
    """
    Annotates based on token patterns, which should be provided as a list of dicts. Each position in the list denotes a
    token position, e.g.: [{'is_initial': True}, {'min_len': 3}] matches sequences of two tokens, where the first one is
    an initial, and the second one is at least 3 characters long.

    Arguments:
        pattern: The pattern
        ds: Any datastructures, that can be used for lookup or other logic
    """

    def __init__(self, pattern: list[dict], *args, ds: Optional[dd.ds.DsCollection] = None, **kwargs) -> None:

        self.pattern = pattern
        self.ds = ds
        super().__init__(*args, **kwargs)

    def match(self, token: dd.tokenize.Token, token_pattern: dict) -> bool:
        """Match token against a single element of a token pattern (i.e. this token against this pattern, no sequences
        involved)."""

        if len(token_pattern) > 1:
            raise ValueError(f"Cannot parse token pattern ({token_pattern}) with more than 1 key")

        func, value = next(iter(token_pattern.items()))

        # TODO: Possibly make this logic more generic?
        if func == "and":
            return all(self.match(token, x) for x in value)
        elif func == "or":
            return any(self.match(token, x) for x in value)
        elif func == "equal":
            return token.text == value
        elif func == "min_len":
            return len(token.text) >= value
        elif func == "starts_with_capital":
            return token.text[0].isupper() == value
        elif func == "is_initial":
            return (len(token.text) == 1 and token.text[0].isupper()) == value
        elif func == "lookup":
            return token.text in self.ds[value]
        elif func == "neg_lookup":
            return token.text not in self.ds[value]
        elif func == "lowercase_lookup":
            return token.text.lower() in self.ds[value]
        elif func == "lowercase_neg_lookup":
            return token.text.lower() not in self.ds[value]
        else:
            raise NotImplementedError(f"No known logic for pattern {func}")

    def match_sequence(
        self, doc: Document, start_token: dd.tokenize.Token, pattern: list[dict], direction: str = "right"
    ) -> Optional[dd.Annotation]:
        """Match the sequence of the pattern at this token position."""

        current_token = start_token
        end_token = start_token

        if direction == "right":
            attr = "next_alpha"
        else:
            attr = "previous_alpha"
            pattern = reversed(pattern)

        for position in pattern:

            if current_token is None or not self.match(current_token, position):
                return None

            end_token = current_token
            current_token = getattr(current_token, attr)()

        if direction == "left":
            start_token, end_token = end_token, start_token

        return dd.Annotation(
            text=doc.text[start_token.start_char : end_token.end_char],
            start_char=start_token.start_char,
            end_char=end_token.end_char,
            tag=self.tag,
            start_token=start_token,
            end_token=end_token,
        )

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:

        annotations = []

        for token in doc.get_tokens():

            annotation = self.match_sequence(doc, token, self.pattern)

            if annotation is not None:
                annotations.append(annotation)

        return annotations


class ContextAnnotator(TokenPatternAnnotator):
    def __init__(self, *args, iterative: Optional[bool] = True, **kwargs):
        self.iterative = iterative
        super().__init__(*args, **kwargs, tag="_")

    def apply_context_pattern(
        self, doc: dd.Document, annotations: dd.AnnotationSet, context_pattern: dict
    ) -> (dd.AnnotationSet, bool):

        new_annotations = dd.AnnotationSet()
        changes = False

        for annotation in annotations:

            tag_min = annotation.tag.split("+")

            if context_pattern['direction'] == "right":
                tag_min = tag_min[-1]
            else:
                tag_min = tag_min[0]

            if not deduce.utils.any_in_text(context_pattern["pre_tag"], tag_min):
                new_annotations.add(annotation)
                continue

            if context_pattern["direction"] == "right":
                start_token = annotation.end_token.next_alpha()
            else:
                start_token = annotation.start_token.previous_alpha()

            new_annotation = self.match_sequence(
                doc, start_token, context_pattern["pattern"], direction=context_pattern["direction"]
            )

            if new_annotation:

                changes = True

                if context_pattern["direction"] == "right":

                    start_char = annotation.start_char
                    end_char = new_annotation.end_char

                    new_annotations.add(
                        dd.Annotation(
                            text=doc.text[start_char:end_char],
                            start_char=start_char,
                            end_char=end_char,
                            start_token=annotation.start_token,
                            end_token=new_annotation.end_token,
                            tag=context_pattern["tag"].format(tag=annotation.tag),
                        )
                    )

                else:

                    start_char = new_annotation.start_char
                    end_char = annotation.end_char

                    new_annotations.add(
                        dd.Annotation(
                            text=doc.text[start_char:end_char],
                            start_char=start_char,
                            end_char=end_char,
                            start_token=new_annotation.start_token,
                            end_token=annotation.end_token,
                            tag=context_pattern["tag"].format(tag=annotation.tag),
                        )
                    )

            else:

                new_annotations.add(annotation)

        return new_annotations, changes

    def _annotate(self, annotations: list[dd.Annotation], doc: dd.Document) -> list[dd.Annotation]:

        changes = False

        for context_pattern in self.pattern:
            c_annotations, c_changes = self.apply_context_pattern(doc, annotations, context_pattern)

            annotations = c_annotations
            changes |= c_changes

        if changes and self.iterative:
            annotations = self._annotate(annotations, doc)

        return annotations

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:

        doc.annotations = self._annotate(list(doc.annotations), doc)
        return []


class BsnAnnotator(dd.process.Annotator):
    """Annotates BSN nummers."""

    def __init__(self, bsn_regexp: str, *args, capture_group: int = 0, **kwargs) -> None:
        self.bsn_regexp = re.compile(bsn_regexp)
        self.capture_group = capture_group
        super().__init__(*args, **kwargs)

    @staticmethod
    def _elfproef(bsn: str) -> bool:

        if len(bsn) != 9 or (any(not char.isdigit() for char in bsn)):
            raise ValueError("Elfproef for testing BSN can only be applied to strings with 9 digits.")

        total = 0

        for char, factor in zip(bsn, [9, 8, 7, 6, 5, 4, 3, 2, -1]):
            total += int(char) * factor

        return total % 11 == 0

    def annotate(self, doc: Document) -> list[Annotation]:

        annotations = []

        for match in self.bsn_regexp.finditer(doc.text):

            text = re.sub(r"\D", "", match.group(self.capture_group))
            start, end = match.span(self.capture_group)

            if self._elfproef(text):
                annotations.append(
                    Annotation(text=text, start_char=start, end_char=end, tag=self.tag, priority=self.priority)
                )

        return annotations


class PhoneNumberAnnotator(dd.process.Annotator):
    """Annotates phone numbers."""

    def __init__(self, phone_regexp: str, *args, min_digits: int = 9, max_digits: int = 11, **kwargs) -> None:

        self.phone_regexp = re.compile(phone_regexp)
        self.min_digits = min_digits
        self.max_digits = max_digits

        super().__init__(*args, **kwargs)

    def annotate(self, doc: Document) -> list[Annotation]:

        annotations = []

        for match in self.phone_regexp.finditer(doc.text):

            digit_len_shift = 0
            left_index_shift = 0
            prefix_with_parens = match.group(1)
            prefix_digits = "0" + re.sub(r"\D", "", match.group(3))
            number_digits = re.sub(r"\D", "", match.group(4))

            # Trim parenthesis
            if prefix_with_parens.startswith("(") and not prefix_with_parens.endswith(")"):
                left_index_shift = 1

            # Check max 1 hyphen
            if len(re.findall("-", match.group(0))) > 1:
                continue

            # Shift num digits for shorter numbers
            if prefix_digits in ["0800", "0900", "0906", "0909"]:
                digit_len_shift = -2

            if (
                (self.min_digits + digit_len_shift)
                <= (len(prefix_digits) + len(number_digits))
                <= (self.max_digits + digit_len_shift)
            ):
                text = match.group(0)[left_index_shift:]
                start_char, end_char = match.span(0)
                start_char += left_index_shift

                annotations.append(
                    Annotation(
                        text=text, start_char=start_char, end_char=end_char, tag=self.tag, priority=self.priority
                    )
                )

        return annotations
