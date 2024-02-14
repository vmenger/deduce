"""Contains components for annotating."""

import re
import warnings
from re import Pattern
from typing import Literal, Optional, Tuple

import docdeid as dd
from docdeid import Annotation, Document, Tokenizer
from docdeid.process import RegexpAnnotator

from deduce.str.processor import TitleCase
from deduce.utils import str_match

warnings.simplefilter(action="default")

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


title_caser = TitleCase()


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

        # String matching functions
        if func == "equal":
            return kwargs.get("token").text == value
        if func == "re_match":
            return re.match(value, kwargs.get("token").text) is not None
        if func == "is_initial":
            warnings.warn(
                "is_initial matcher pattern is deprecated and will be removed "
                "in a future version",
                DeprecationWarning,
            )
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

        # Lookup functions
        if func == "lookup":
            lookup_value, used_ds = _PatternPositionMatcher.get_lookup_values(
                kwargs, value
            )
            return lookup_value in used_ds
        if func == "title_case_lookup":
            lookup_value, used_ds = _PatternPositionMatcher.get_lookup_values(
                kwargs, value, title_caser
            )
            return lookup_value in used_ds
        if func == "neg_lookup":
            lookup_value, used_ds = _PatternPositionMatcher.get_lookup_values(
                kwargs, value
            )
            return lookup_value not in used_ds

        # Combination functions
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

    @staticmethod
    def get_lookup_values(
        kwargs,
        value: str,
        processor: dd.str.StringModifier = None,
    ) -> Tuple[str | list[str], dd.ds.lookup.LookupStructure]:
        """Get the lookup value for a token given the lookup structure."""
        used_ds = kwargs.get("ds")[value]
        text = kwargs.get("token").text
        text = processor.process(text) if processor else text
        if isinstance(used_ds, dd.ds.lookup.LookupTrie):
            lookup_value = [text]
        else:
            lookup_value = text
        return lookup_value, used_ds


class TokenPatternAnnotator(dd.process.Annotator):
    """
    Annotates based on token patterns, which should be provided as a list of dicts. Each
    position in the list denotes a token position, e.g.: [{'is_initial': True},
    {'like_name': True}] matches sequences of two tokens, where the first one is an
    initial, and the second one is like a name. The entire sequence is annotated.
    If the first token is a lookup, these are located first and the pattern is
    subsequently matched.

    Arguments:
        pattern: The pattern
        ds: Any datastructures, that can be used for lookup or other logic
        skip: Any string values that should be skipped in matching (e.g. periods)
        use_start_words: Whether to use the start words speedup for matching
    """

    def __init__(
        self,
        pattern: list[dict],
        *args,
        ds: Optional[dd.ds.DsCollection] = None,
        skip: Optional[list[str]] = None,
        use_start_words: Optional[bool] = True,
        **kwargs,
    ) -> None:
        self.pattern = pattern
        self.skip = set(skip or [])

        self._start_words = None
        self._matching_pipeline = None
        self.ds = ds

<<<<<<< HEAD
        if use_start_words and len(self.pattern) > 0 and "lookup" in self.pattern[0]:
=======
        if len(self.pattern) > 0 and "lookup" in self.pattern[0]:
>>>>>>> feature_branch/recall_boost
            if self.ds is None:
                raise RuntimeError(
                    "Created pattern with lookup in TokenPatternAnnotator, but "
                    "no lookup structures provided."
                )

            lookup_list = self.ds[self.pattern[0]["lookup"]]

            if not isinstance(lookup_list, dd.ds.LookupSet):
                raise ValueError(
                    f"Expected a LookupSet, but got a " f"{type(lookup_list)}."
                )

            self._start_words = lookup_list.items()
            self._matching_pipeline = lookup_list.matching_pipeline

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
        pattern: list[dict],
        start_token: dd.tokenizer.Token,
        direction: Literal["left", "right"] = "right",
        skip: Optional[set[str]] = None,
    ) -> Optional[dd.Annotation]:
        """
        Sequentially match a pattern against a specified start_token.

        Args:
            pattern: The pattern to match.
            start_token: The start token to match.
            direction: The direction to match, choice of "left" or "right".
            skip: Any string values that should be skipped in matching.

        Returns:
              An Annotation if matching is possible, None otherwise.
        """

        # why is this not self.skip???
        skip = skip or set()

        attr = _DIRECTION_MAP[direction]["attr"]
        pattern = _DIRECTION_MAP[direction]["order"](pattern)

        match_tokens = []
        current_token = start_token

        for pattern_position in pattern:
            if current_token is None or not _PatternPositionMatcher.match(
                pattern_position=pattern_position, token=current_token, ds=self.ds
            ):
                return None

            match_tokens.append(current_token)
            current_token = self._get_chained_token(current_token, attr, skip)

        # reverse result if neccessary
        match_tokens = list(_DIRECTION_MAP[direction]["order"](match_tokens))

        return match_tokens

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:
        """
        Annotate the document, by matching the pattern against all tokens.

        Args:
            doc: The document being processed.

        Returns:
            A list of Annotation.
        """

        annotations = []

        tokens = doc.get_tokens()

        if self._start_words is not None:
            # add expander here in recall booster setting.
            tokens = tokens.token_lookup(
                lookup_values=self._start_words,
                matching_pipeline=self._matching_pipeline,
            )

        for token in tokens:
<<<<<<< HEAD
            sequence_match = self._match_sequence(
                self.pattern, token, direction="right", skip=self.skip
            )
            if not sequence_match:
                continue
            start_token = sequence_match[0]
            end_token = sequence_match[-1]
            annotations.append(
                self._create_annotation(doc.text, start_token, end_token)
=======
            annotation = self._match_sequence(
                doc.text, self.pattern, token, direction="right", skip=self.skip
>>>>>>> feature_branch/recall_boost
            )

        return annotations

    def _create_annotation(
        self, text: str, start_token: dd.Token, end_token: dd.Token
    ) -> dd.Annotation:
        return dd.Annotation(
            text=text[start_token.start_char : end_token.end_char],
            start_char=start_token.start_char,
            end_char=end_token.end_char,
            tag=self.tag,
            priority=self.priority,
            start_token=start_token,
            end_token=end_token,
        )


class ContextAnnotator(TokenPatternAnnotator):
    """
    Extends existing annotations to the left or right, based on specified patterns.

    Args:
        ds: Any datastructures, that can be used for lookup or other logic
        iterative: Whether the extension process should repeat, or stop after one
        iteration.
    """

    def __init__(
        self,
        *args,
        ds: Optional[dd.ds.DsCollection] = None,
        iterative: bool = True,
        **kwargs,
    ) -> None:
        self.iterative = iterative
        super().__init__(*args, **kwargs, ds=ds, tag="_")

    def _apply_context_pattern(
        self, text: str, annotations: dd.AnnotationSet, context_pattern: dict
    ) -> dd.AnnotationSet:
        direction = context_pattern["direction"]
        skip = set(context_pattern.get("skip", []))

        for annotation in annotations.copy():
            tag = list(_DIRECTION_MAP[direction]["order"](annotation.tag.split("+")))[
                -1
            ]

            if tag not in context_pattern["pre_tag"]:
                continue

            attr = _DIRECTION_MAP[direction]["attr"]
            start_token = self._get_chained_token(
                _DIRECTION_MAP[direction]["start_token"](annotation), attr, skip
            )
            sequence_match = self._match_sequence(
                context_pattern["pattern"],
                start_token,
                direction=direction,
                skip=skip,
            )
            if not sequence_match:
                continue

            new_annotation = self._create_annotation(
                text, sequence_match[0], sequence_match[-1]
            )

            left_ann, right_ann = _DIRECTION_MAP[direction]["order"](
                (annotation, new_annotation)
            )

            merged_annotation = dd.Annotation(
                text=text[left_ann.start_char : right_ann.end_char],
                start_char=left_ann.start_char,
                end_char=right_ann.end_char,
                start_token=left_ann.start_token,
                end_token=right_ann.end_token,
                tag=context_pattern["tag"].format(tag=annotation.tag),
                priority=annotation.priority,
            )

            annotations.remove(annotation)
            annotations.add(merged_annotation)

        return annotations

    def _annotate(self, text: str, annotations: dd.AnnotationSet) -> dd.AnnotationSet:
        """
        Does the annotation, by calling _apply_context_pattern, and then optionally
        recursing. Also keeps track of the (un)changed annotations, so they are not
        repeatedly processed.

        Args:
            text: The input text.
            annotations: The input annotations.

        Returns:
            An extended set of annotations, based on the patterns provided.
        """

        original_annotations = annotations.copy()

        for context_pattern in self.pattern:
            annotations = self._apply_context_pattern(
                text, annotations, context_pattern
            )

        if self.iterative:
            changed = dd.AnnotationSet(annotations.difference(original_annotations))
            annotations = dd.AnnotationSet(
                annotations.intersection(original_annotations)
            )

            if changed:
                annotations.update(self._annotate(text, changed))

        return annotations

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:
        """
        Wrapper for annotating.

        Args:
            doc: The document to process.

        Returns:
            An empty list, as annotations are modified and not added.
        """

        doc.annotations = self._annotate(doc.text, doc.annotations)
        return []


class PatientNameAnnotator(dd.process.Annotator):
    """
    Annotates patient names, based on information present in document metadata. This
    class implements logic for detecting first name(s), initials and surnames.

    Args:
        tokenizer: A tokenizer, that is used for breaking up the patient surname
            into multiple tokens.
    """

    def __init__(self, tokenizer: Tokenizer, *args, **kwargs) -> None:
        self.tokenizer = tokenizer
        self.skip = [".", "-", " "]

        super().__init__(*args, **kwargs)

    @staticmethod
    def _match_first_names(
        doc: dd.Document, token: dd.Token
    ) -> Optional[tuple[dd.Token, dd.Token]]:
        for first_name in doc.metadata["patient"].first_names:
            if str_match(token.text, first_name) or (
                len(token.text) > 3
                and str_match(token.text, first_name, max_edit_distance=1)
            ):
                return token, token

        return None

    @staticmethod
    def _match_initial_from_name(
        doc: dd.Document, token: dd.Token
    ) -> Optional[tuple[dd.Token, dd.Token]]:
        for _, first_name in enumerate(doc.metadata["patient"].first_names):
            if str_match(token.text, first_name[0]):
                next_token = token.next()

                if (next_token is not None) and str_match(next_token.text, "."):
                    return token, next_token

                return token, token

        return None

    @staticmethod
    def _match_initials(
        doc: dd.Document, token: dd.Token
    ) -> Optional[tuple[dd.Token, dd.Token]]:
        if str_match(token.text, doc.metadata["patient"].initials):
            return token, token

        return None

    def next_with_skip(self, token: dd.Token) -> Optional[dd.Token]:
        """Find the next token, while skipping certain punctuation."""

        while True:
            token = token.next()

            if (token is None) or (token not in self.skip):
                break

        return token

    def _match_surname(
        self, doc: dd.Document, token: dd.Token
    ) -> Optional[tuple[dd.Token, dd.Token]]:
        if doc.metadata["surname_pattern"] is None:
            doc.metadata["surname_pattern"] = self.tokenizer.tokenize(
                doc.metadata["patient"].surname
            )

        surname_pattern = doc.metadata["surname_pattern"]

        surname_token = surname_pattern[0]
        start_token = token

        while True:
            if not str_match(surname_token.text, token.text, max_edit_distance=1):
                return None

            match_end_token = token

            surname_token = self.next_with_skip(surname_token)
            token = self.next_with_skip(token)

            if surname_token is None:
                return start_token, match_end_token  # end of pattern

            if token is None:
                return None  # end of tokens

    def annotate(self, doc: Document) -> list[Annotation]:
        """
        Annotates the document, based on the patient metadata.

        Args:
            doc: The input document.

        Returns: A document with any relevant Annotations added.
        """

        if doc.metadata is None or doc.metadata["patient"] is None:
            return []

        matcher_to_attr = {
            self._match_first_names: ("first_names", "voornaam_patient"),
            self._match_initial_from_name: ("first_names", "initiaal_patient"),
            self._match_initials: ("initials", "initiaal_patient"),
            self._match_surname: ("surname", "achternaam_patient"),
        }

        matchers = []
        patient_metadata = doc.metadata["patient"]

        for matcher, (attr, tag) in matcher_to_attr.items():
            if getattr(patient_metadata, attr) is not None:
                matchers.append((matcher, tag))

        annotations = []

        for token in doc.get_tokens():
            for matcher, tag in matchers:
                match = matcher(doc, token)

                if match is None:
                    continue

                start_token, end_token = match

                annotations.append(
                    dd.Annotation(
                        text=doc.text[start_token.start_char : end_token.end_char],
                        start_char=start_token.start_char,
                        end_char=end_token.end_char,
                        tag=tag,
                        priority=self.priority,
                        start_token=start_token,
                        end_token=end_token,
                    )
                )

        return annotations


class RegexpPseudoAnnotator(RegexpAnnotator):
    """
    Regexp annotator that filters out matches preceded or followed by certain terms.
    Currently matches on sequential alpha characters preceding or following the match.
    This annotator does not depend on any tokenizer.

    Args:
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


class RegexpAnnotatorPrematchReplacement(RegexpAnnotator):
    """replaces the keyword pre_match_words with a join of the
    pre_match_words list"""

    def __init__(
        self,
<<<<<<< HEAD
        regexp_pattern: Pattern | str,
        *args,
        capturing_group: int = 0,
        pre_match_words: list[str] | None = None,
        **kwargs,
    ) -> None:
        if pre_match_words is None:
            raise ValueError(
                "pre_match_words cannot be None when using this regex annotator"
            )
=======
        regexp_pattern: str,
        pre_match_words: list[str],
        *args,
        capturing_group: int = 0,
        **kwargs,
    ) -> None:
>>>>>>> feature_branch/recall_boost
        pre_match_words.sort(key=len, reverse=True)
        regexp_pattern = regexp_pattern.replace(
            "pre_match_words", "|".join(pre_match_words)
        )
        super().__init__(
            regexp_pattern,
            *args,
            capturing_group=capturing_group,
            pre_match_words=pre_match_words,
            **kwargs,
        )


class BsnAnnotator(dd.process.Annotator):
    """
    Annotates Burgerservicenummer (BSN), according to the elfproef logic.
    See also: https://nl.wikipedia.org/wiki/Burgerservicenummer

    Args:
        bsn_regexp: A regexp to match potential BSN nummers. The simplest form could be
            9-digit numbers, but matches with periods or other punctutation can also be
            accepted. Any non-digit characters are removed from the match before
            the elfproef is applied.
        capture_group: The regexp capture group to consider.
    """

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
    """
    Annotates phone numbers, based on a regexp and min and max number of digits.
    Additionally employs some logic like detecting parentheses and hyphens.

    Args:
        phone_regexp: The regexp to detect phone numbers.
        min_digits: The minimum number of digits that need to be present.
        max_digits: The maximum number of digits that need to be present.
    """

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


class TargetWordTokenPatternAnnotator(TokenPatternAnnotator):
    """
    Annotates based on token patterns like the TokenPatternAnnotator. However, in this
    annotator target words ore obligatory to target the pattern matching, the target word
    is allowed at any pattern position (rather than only start word) and the
    annotation can be a subset of the matched sequence of tokens.

    Arguments:
        pattern: The pattern
        ds: Any datastructures, that can be used for lookup or other logic
        skip: Any string values that should be skipped in matching (e.g. periods)
        target_words_lookup: The name in ds of the target words
        annotate_pattern_indices: The indices of the pattern to annotate
    """

    def __init__(
        self,
        pattern: list[dict],
        target_words_lookup: str,
        annotate_pattern_indices: list[int],
        ds: dd.ds.DsCollection,
        *args,
        skip: Optional[list[str]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            pattern=pattern, *args, ds=ds, use_start_words=False, skip=skip, **kwargs
        )

        self.window_target = target_words_lookup
        self.annotation_start_index = min(annotate_pattern_indices)
        self.annotation_end_index = max(annotate_pattern_indices)

        # verify correctness of target window and pattern lookups against ds
        pattern_lookups = self.get_pattern_lookups(self.pattern)
        if self.window_target not in pattern_lookups:
            raise ValueError(f"window_target {self.window_target} not found in pattern")
        for pattern_lookup in pattern_lookups.keys():
            if pattern_lookup not in ds:
                raise ValueError(f"lookup {pattern_lookup} not found in ds")

        # Initialize target words
        if not isinstance(self.ds[self.window_target], dd.ds.LookupSet):
            raise ValueError(
                f"Expected a LookupSet, but got a "
                f"{type(self.ds[self.window_target])}."
            )
        self._target_words = self.ds[self.window_target].items()
        self._matching_pipeline = self.ds[self.window_target].matching_pipeline

        # Initialize shift wrt target word
        self._shift = -pattern_lookups[self.window_target]

    def get_pattern_lookups(self, pattern: list[dict]):
        # check for {"lookup": "value"} values in pattern
        result_dict = {}
        for i, pattern_position in enumerate(pattern):
            assert len(pattern_position) == 1
            key, value = next(iter(pattern_position.items()))
            # Extend to title case lookup?
            if key == "lookup":
                if value in result_dict:
                    raise ValueError(f"lookup {value} used multiple times in pattern")
                result_dict[value] = i
            # handle nested patterns
            elif isinstance(value, list):
                d = self.get_pattern_lookups(value)
                for lookup_name in d.keys():
                    if lookup_name in result_dict:
                        raise ValueError(
                            f"lookup {value} used multiple times in pattern"
                        )
                    result_dict[lookup_name] = i

        return result_dict

    def get_start_index(self, tokens: dd.tokenizer.TokenList, target_token: dd.Token):
        i = 0
        target_index = tokens.token_index(target_token)
        while i < abs(self._shift):
            if self._shift > 0:
                target_index += 1
            else:
                target_index -= 1
            if target_index < 0 or target_index >= len(tokens):
                return None
            if tokens[target_index].text not in self.skip:
                i += 1
        return target_index

    def annotate(self, doc: dd.Document) -> list[dd.Annotation]:
        """
        Annotate the document, by matching the pattern against start positions wrt target words.

        Args:
            doc: The document being processed.

        Returns:
            A list of Annotations.
        """

        annotations = []
        tokens = doc.get_tokens()

        target_tokens = tokens.token_lookup(
            lookup_values=self._target_words,
            matching_pipeline=self._matching_pipeline,
        )

        for target_token in target_tokens:
            start_index = self.get_start_index(tokens, target_token)
            if start_index is None:
                continue
            tokens.token_index(target_token) + self._shift
            if start_index < 0:
                continue

            sequence_match = self._match_sequence(
                self.pattern,
                tokens[start_index],
                direction="right",
                skip=self.skip,
            )
            if not sequence_match:
                continue

            start_token = sequence_match[self.annotation_start_index]
            end_token = sequence_match[self.annotation_end_index]
            annotations.append(
                self._create_annotation(doc.text, start_token, end_token)
            )

        return annotations
