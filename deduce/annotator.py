import re
from typing import Literal, Optional

import docdeid as dd
from docdeid import Annotation, Document
from docdeid.process import RegexpAnnotator

import deduce.utils

_DIRECTION_MAP = {
    "left": {
        "attr": "previous",
        "order": reversed,
        "start_token": lambda annotation: annotation.start_token,
    },
    "right": {
        "attr": "next",
        "order": lambda pattern: pattern,
        "start_token": lambda annotation: annotation.end_token,
    },
}


class _PatternPositionMatcher:  # pylint: disable=R0903
    """Checks if a token matches against a single pattern."""

    @classmethod
    def match(cls, pattern_position: dict, **kwargs) -> bool:  # pylint: disable=R0911
        """
        Matches a pattern position (a dict with one key). Other information should be
        presented as kwargs.

        Args:
            pattern_position: A dictionary with a single key, e.g. {'is_initial': True}
            kwargs: Any other information, like the token or ds

        Returns:
            True if the pattern position matches, false otherwise.
        """

        if len(pattern_position) > 1:
            raise ValueError(
                f"Cannot parse token pattern ({pattern_position}) with more than 1 key"
            )

        func, value = next(iter(pattern_position.items()))

        if func == "equal":
            return kwargs.get("token").text == value
        if func == "re_match":
            return re.match(value, kwargs.get("token").text) is not None
        if func == "is_initial":
            return (
                (
                    len(kwargs.get("token").text) == 1
                    and kwargs.get("token").text[0].isupper()
                )
                or kwargs.get("token").text in {"Ch", "Chr", "Ph", "Th"}
            ) == value
        if func == "is_initials":
            return (
                len(kwargs.get("token").text) <= 4
                and kwargs.get("token").text.isupper()
            ) == value
        if func == "like_name":
            return (
                len(kwargs.get("token").text) >= 3
                and kwargs.get("token").text.istitle()
                and not any(ch.isdigit() for ch in kwargs.get("token").text)
            ) == value
        if func == "lookup":
            return kwargs.get("token").text in kwargs.get("ds")[value]
        if func == "neg_lookup":
            return kwargs.get("token").text not in kwargs.get("ds")[value]
        if func == "lowercase_lookup":
            return kwargs.get("token").text.lower() in kwargs.get("ds")[value]
        if func == "lowercase_neg_lookup":
            return kwargs.get("token").text.lower() not in kwargs.get("ds")[value]
        if func == "and":
            return all(
                _PatternPositionMatcher.match(pattern_position=x, **kwargs)
                for x in value
            )
        if func == "or":
            return any(
                _PatternPositionMatcher.match(pattern_position=x, **kwargs)
                for x in value
            )

        raise NotImplementedError(f"No known logic for pattern {func}")


class TokenPatternAnnotator(dd.process.Annotator):
    """
    Annotates based on token patterns, which should be provided as a list of dicts. Each
    position in the list denotes a token position, e.g.: [{'is_initial': True},
    {'like_name': True}] matches sequences of two tokens, where the first one is an
    initial, and the second one is like a name.

    Arguments:
        pattern: The pattern
        ds: Any datastructures, that can be used for lookup or other logic
        skip: Any string values that should be skipped in matching (e.g. periods)
    """

    def __init__(
        self,
        pattern: list[dict],
        *args,
        ds: Optional[dd.ds.DsCollection] = None,
        skip: Optional[list[str]] = None,
        **kwargs,
    ) -> None:
        self.pattern = pattern
        self.ds = ds
        self.skip = set(skip or [])

        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_chained_token(
        token: dd.Token, attr: str, skip: set[str]
    ) -> Optional[dd.Token]:
        while True:
            token = getattr(token, attr)()

            if token is None or token.text not in skip:
                break

        return token

    def _match_sequence(  # pylint: disable=R0913
        self,
        doc: Document,
        pattern: list[dict],
        start_token: dd.tokenize.Token,
        direction: Literal["left", "right"] = "right",
        skip: Optional[set[str]] = None,
    ) -> Optional[dd.Annotation]:
        """
        Sequentially match a pattern against a specified start_token.

        Args:
            doc: The document that is being processed.
            pattern: The pattern to match.
            start_token: The start token to match.
            direction: The direction to match, choice of "left" or "right".
            skip: Any string values that should be skipped in matching.

        Returns:
              An Annotation if matching is possible, None otherwise.
        """

        skip = skip or set()

        attr = _DIRECTION_MAP[direction]["attr"]
        pattern = _DIRECTION_MAP[direction]["order"](pattern)

        current_token = start_token
        end_token = start_token

        for pattern_position in pattern:
            if current_token is None or not _PatternPositionMatcher.match(
                pattern_position=pattern_position, token=current_token, ds=self.ds
            ):
                return None

            end_token = current_token
            current_token = self._get_chained_token(current_token, attr, skip)

        start_token, end_token = _DIRECTION_MAP[direction]["order"](
            (start_token, end_token)
        )

        return dd.Annotation(
            text=doc.text[start_token.start_char : end_token.end_char],
            start_char=start_token.start_char,
            end_char=end_token.end_char,
            tag=self.tag,
            priority=self.priority,
            start_token=start_token,
            end_token=end_token,
        )

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:
        """
        Annotate the document, by matching the pattern against all tokens.

        Args:
            doc: The document being processed.

        Returns:
            A list of Annotation.
        """

        return [
            annotation
            for token in doc.get_tokens()
            if (
                annotation := self._match_sequence(
                    doc, self.pattern, token, direction="right", skip=self.skip
                )
            )
            is not None
        ]


class ContextAnnotator(TokenPatternAnnotator):
    """
    Extends existing annotations to the left or right, based on specified patterns.

    Args:
        iterative: Whether the extension process should recurse, or stop after one
        iteration.
    """

    def __init__(self, *args, iterative: bool = True, **kwargs) -> None:
        self.iterative = iterative
        super().__init__(*args, **kwargs, tag="_")

    def _apply_context_pattern(
        self, doc: dd.Document, annotations: dd.AnnotationSet, context_pattern: dict
    ) -> dd.AnnotationSet:
        new_annotations = dd.AnnotationSet()
        direction = context_pattern["direction"]

        for annotation in annotations:
            tag = list(_DIRECTION_MAP[direction]["order"](annotation.tag.split("+")))[
                -1
            ]
            skip = set(context_pattern.get("skip", []))

            if not deduce.utils.any_in_text(context_pattern["pre_tag"], tag):
                new_annotations.add(annotation)
                continue

            attr = _DIRECTION_MAP[direction]["attr"]
            start_token = self._get_chained_token(
                _DIRECTION_MAP[direction]["start_token"](annotation), attr, skip
            )
            new_annotation = self._match_sequence(
                doc,
                context_pattern["pattern"],
                start_token,
                direction=direction,
                skip=skip,
            )

            if new_annotation:
                left_ann, right_ann = _DIRECTION_MAP[direction]["order"](
                    (annotation, new_annotation)
                )

                new_annotations.add(
                    dd.Annotation(
                        text=doc.text[left_ann.start_char : right_ann.end_char],
                        start_char=left_ann.start_char,
                        end_char=right_ann.end_char,
                        start_token=left_ann.start_token,
                        end_token=right_ann.end_token,
                        tag=context_pattern["tag"].format(tag=annotation.tag),
                        priority=annotation.priority,
                    )
                )
            else:
                new_annotations.add(annotation)

        return new_annotations

    def _annotate(
        self, doc: dd.Document, annotations: list[dd.Annotation]
    ) -> list[dd.Annotation]:
        original_annotations = annotations

        for context_pattern in self.pattern:
            annotations = self._apply_context_pattern(doc, annotations, context_pattern)

        if self.iterative and (annotations != original_annotations):
            annotations = self._annotate(doc, annotations)

        return annotations

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:
        """
        Wrapper for annotating.

        Args:
            doc: The document to process.

        Returns:
            An empty list, as annotations are modified and not added.
        """

        doc.annotations = self._annotate(doc, list(doc.annotations))
        return []


class RegexpPseudoAnnotator(RegexpAnnotator):
    """
    Regexp annotator that filters out matches preceded or followed by certain terms.
    Currently matches on sequential alhpa characters preceding or following the match.

    pre_pseudo: A list of strings that invalidate a match when preceding it
    post_pseudo: A list of strings that invalidate a match when following it
    lowercase: Whether to match lowercase
    """

    def __init__(
        self,
        *args,
        pre_pseudo: Optional[list[str]] = None,
        post_pseudo: Optional[list[str]] = None,
        lowercase: bool = True,
        **kwargs,
    ) -> None:

        self.pre_pseudo = set(pre_pseudo or [])
        self.post_pseudo = set(post_pseudo or [])
        self.lowercase = lowercase

        super().__init__(*args, **kwargs)

    @staticmethod
    def _is_word_char(char: str) -> bool:
        """
        Determines whether a character can be part of a word.

        Args:
            char: The character

        Returns: True when the character can be part of a word, false otherwise.
        """

        return char.isalpha()

    def _get_previous_word(self, char_index: int, text: str) -> str:
        """
        Get the previous word starting at some character index.

        Args:
            char_index: The character index to start searching.
            text: The text.

        Returns: The previous word, or an empty string if at beginning of text.
        """

        text = text[:char_index].strip()
        result = ""

        for ch in text[::-1]:

            if not self._is_word_char(ch):
                break

            result = ch + result

        return result.strip()

    def _get_next_word(self, char_index: int, text: str) -> str:
        """
        Get the next word starting at some character index.

        Args:
            char_index: The character index to start searching.
            text: The text.

        Returns: The next word, or an empty string if at end of text.
        """

        text = text[char_index:].strip()
        result = ""

        for ch in text:

            if not self._is_word_char(ch):
                break

            result = result + ch

        return result

    def _validate_match(self, match: re.Match, doc: Document) -> bool:
        """
        Validate match, by checking the preceding or following words against the defined
        pseudo sets.

        Args:
            match: The regexp match.
            doc: The doc object.

        Returns: True when the match is valid, False when invalid.
        """

        start_char, end_char = match.span(0)

        previous_word = self._get_previous_word(start_char, doc.text)
        next_word = self._get_next_word(end_char, doc.text)

        if self.lowercase:
            previous_word = previous_word.lower()
            next_word = next_word.lower()

        return (previous_word not in self.pre_pseudo) and (
            next_word not in self.post_pseudo
        )


class BsnAnnotator(dd.process.Annotator):
    """Annotates BSN nummers."""

    def __init__(
        self, bsn_regexp: str, *args, capture_group: int = 0, **kwargs
    ) -> None:
        self.bsn_regexp = re.compile(bsn_regexp)
        self.capture_group = capture_group
        super().__init__(*args, **kwargs)

    @staticmethod
    def _elfproef(bsn: str) -> bool:
        if len(bsn) != 9 or (any(not char.isdigit() for char in bsn)):
            raise ValueError(
                "Elfproef for testing BSN can only be applied to strings with 9 digits."
            )

        total = 0

        for char, factor in zip(bsn, [9, 8, 7, 6, 5, 4, 3, 2, -1]):
            total += int(char) * factor

        return total % 11 == 0

    def annotate(self, doc: Document) -> list[Annotation]:
        annotations = []

        for match in self.bsn_regexp.finditer(doc.text):

            text = match.group(self.capture_group)
            digits = re.sub(r"\D", "", text)

            start, end = match.span(self.capture_group)

            if self._elfproef(digits):
                annotations.append(
                    Annotation(
                        text=text,
                        start_char=start,
                        end_char=end,
                        tag=self.tag,
                        priority=self.priority,
                    )
                )

        return annotations


class PhoneNumberAnnotator(dd.process.Annotator):
    """Annotates phone numbers."""

    def __init__(
        self,
        phone_regexp: str,
        *args,
        min_digits: int = 9,
        max_digits: int = 11,
        **kwargs,
    ) -> None:
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
            if prefix_with_parens.startswith("(") and not prefix_with_parens.endswith(
                ")"
            ):
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
                        text=text,
                        start_char=start_char,
                        end_char=end_char,
                        tag=self.tag,
                        priority=self.priority,
                    )
                )

        return annotations
