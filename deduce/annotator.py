"""Contains components for annotating."""

import re
import warnings
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

import docdeid as dd
from deduce.utils import str_match
from docdeid import Annotation, Document, Token, Tokenizer
from docdeid.direction import Direction
from docdeid.process import Annotator, RegexpAnnotator
from docdeid.process.annotator import (
    as_token_pattern,
    SequenceAnnotator,
    SequencePattern,
)

warnings.simplefilter(action="default")


@dataclass
class ContextPattern:
    """
    Pattern for matching a sequence of tokens anchored on a certain starting tag.
    """
    pre_tag: Optional[set[str]]
    tag: str
    seq_pattern: SequencePattern


class ContextAnnotator(Annotator):
    """
    Extends existing annotations to the left or right, based on specified patterns.

    Args:
        ds: Any datastructures, that can be used for lookup or other logic
        iterative: Whether the extension process should repeat, or stop after one
        iteration.
    """

    def __init__(
        self,
        pattern: list[dict], # TODO Rename to "patterns" or similar.
        *args,
        ds: Optional[dd.ds.DsCollection] = None,
        iterative: bool = True,
        **kwargs,
    ) -> None:
        self.ds = ds
        self.iterative = iterative
        self._patterns = [
            ContextPattern(pat['pre_tag'],
                           pat['tag'],
                           SequencePattern(
                               Direction.from_string(pat.get('direction', "right")),
                               set(pat.get('skip', ())),
                               list(map(as_token_pattern, pat['pattern']))))
            for pat in pattern
        ]
        super().__init__(*args, **kwargs, tag='_')  # XXX Not sure why exactly '_'.

    def _apply_context_pattern(
        self,
        doc: Document,
        context_pattern: ContextPattern,
        orig_annos: dd.AnnotationSet,
    ) -> dd.AnnotationSet:

        # TODO Maybe we should index all annotations here, not just the `new` ones.
        annos_by_token = orig_annos.annos_by_token(doc)

        return dd.AnnotationSet(
            self._maybe_merge_anno(anno, context_pattern, doc, annos_by_token)
            for anno in orig_annos
        )

    def _maybe_merge_anno(
        self,
        annotation: Annotation,
        context_pattern: ContextPattern,
        doc: Document,
        annos_by_token: defaultdict[str, Iterable[Annotation]],
    ) -> Annotation:

        dir_ = context_pattern.seq_pattern.direction
        tag = list(dir_.iter(annotation.tag.split("+")))[-1]

        if tag not in context_pattern.pre_tag:
            return annotation

        anno_start = (annotation.end_token if dir_ is Direction.RIGHT else
                      annotation.start_token)
        skip = context_pattern.seq_pattern.skip
        tokens = (token for token in anno_start.iter_to(dir_)
                  if token.text not in skip)
        try:
            start_token = next(tokens)
        except StopIteration:
            return annotation

        new_annotation = self._match_sequence(doc,
                                              context_pattern.seq_pattern,
                                              start_token,
                                              annos_by_token,
                                              self.ds)

        if not new_annotation:
            return annotation

        left_ann, right_ann = dir_.iter((annotation, new_annotation))

        return Annotation(
            text=doc.text[left_ann.start_char : right_ann.end_char],
            start_char=left_ann.start_char,
            end_char=right_ann.end_char,
            start_token=left_ann.start_token,
            end_token=right_ann.end_token,
            tag=context_pattern.tag.format(tag=annotation.tag),
            priority=annotation.priority,
        )

    def _get_annotations(
        self, doc: Document, orig_annos: Optional[dd.AnnotationSet] = None
    ) -> dd.AnnotationSet:
        """
        Computes the annotation for `doc` and returns it.

        Does this by calling _apply_context_pattern and then optionally recursing.
        Also keeps track of the (un)changed annotations, so they are not repeatedly
        processed.

        Args:
            doc: The input document.
            orig_annos: Current set of annotations. If `None`, `doc.annotations` will
                        be consulted.

        Returns:
            An extended set of annotations, based on the patterns provided.
        """

        if orig_annos is None:
            orig_annos = doc.annotations
        annotations = orig_annos.copy()

        for context_pattern in self._patterns:
            annotations = self._apply_context_pattern(doc, context_pattern, annotations)

        if self.iterative and (new := dd.AnnotationSet(annotations - orig_annos)):
            # XXX Are we sure that other annotations than `new` don't matter anymore
            #  to the operation of the `_get_annotations` method?
            annotations = dd.AnnotationSet(
                (annotations - new) | self._get_annotations(doc, new)
            )

        return annotations

    def annotate(self, doc: Document) -> list[Annotation]:
        """
        Wrapper for annotating.

        Args:
            doc: The document to process.

        Returns:
            An empty list, as annotations are modified and not added.
        """

        doc.annotations = self._get_annotations(doc)
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
        doc: Document, token: Token
    ) -> Optional[tuple[Token, Token]]:

        for first_name in doc.metadata["patient"].first_names:

            if str_match(token.text, first_name) or (
                len(token.text) > 3
                and str_match(token.text, first_name, max_edit_distance=1)
            ):
                return token, token

        return None

    @staticmethod
    def _match_initial_from_name(
        doc: Document, token: Token
    ) -> Optional[tuple[Token, Token]]:

        for _, first_name in enumerate(doc.metadata["patient"].first_names):
            if str_match(token.text, first_name[0]):
                next_token = token.next()

                if (next_token is not None) and str_match(next_token.text, "."):
                    return token, next_token

                return token, token

        return None

    @staticmethod
    def _match_initials(doc: Document, token: Token) -> Optional[tuple[Token, Token]]:

        if str_match(token.text, doc.metadata["patient"].initials):
            return token, token

        return None

    def next_with_skip(self, token: Token) -> Optional[Token]:
        """Find the next token, while skipping certain punctuation."""

        while True:
            token = token.next()

            if (token is None) or (token not in self.skip):
                break

        return token

    def _match_surname(
        self, doc: Document, token: Token
    ) -> Optional[tuple[Token, Token]]:

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
                    Annotation(
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
    Additionally, employs some logic like detecting parentheses and hyphens.

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


# TODO Drop this. It's confusing given the other annotator of the same name defined
#  in Docdeid.
# For sake of backward compatibility:
TokenPatternAnnotator = SequenceAnnotator