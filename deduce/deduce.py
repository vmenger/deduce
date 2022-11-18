import warnings
from typing import Any

import deprecated
import docdeid as dd

import deduce.backwards_compat
from deduce.annotate.annotation_processing import DeduceMergeAdjacentAnnotations
from deduce.annotate.redact import DeduceRedactor
from deduce.doc_processors import get_doc_processors
from deduce.lookup.lookup_sets import get_lookup_sets
from deduce.tokenize.tokenizer import DeduceTokenizer

warnings.simplefilter(action="once")


class Deduce(dd.DocDeid):
    def __init__(self) -> None:
        super().__init__()
        self.lookup_sets = None
        self._initialize_deduce()

    def _initialize_lookup(self) -> None:
        self.lookup_sets = get_lookup_sets()

    def _initialize_tokenizer(self) -> None:

        merge_terms = dd.ds.LookupSet()
        merge_terms.add_items_from_iterable(["A1", "A2", "A3", "A4", "\n", "\r", "\t"])
        merge_terms += self.lookup_sets["interfixes"]
        merge_terms += self.lookup_sets["prefixes"]

        self.tokenizers["default"] = DeduceTokenizer(merge_terms=merge_terms)

    def _initialize_processors(self) -> None:

        self.processors = get_doc_processors(self.lookup_sets, self.tokenizers["default"])

        self.processors.add_processor(
            "overlap_resolver",
            dd.process.OverlapResolver(
                sort_by=["length"], sort_by_callbacks={"length": lambda x: -x}
            )
        )

        self.processors.add_processor(
            "merge_adjacent_annotations",
            DeduceMergeAdjacentAnnotations(
                slack_regexp=r"[\.\s\-,]?[\.\s]?"
            )
        )

        self.processors.add_processor("redactor", DeduceRedactor(open_char="<", close_char=">"))

    def _initialize_deduce(self) -> None:

        self._initialize_lookup()
        self._initialize_tokenizer()
        self._initialize_processors()


# Backwards compatibility stuff beneath this line.

deduce.backwards_compat.BackwardsCompat.set_deduce_model(Deduce())
deprecation_info = {"version": "2.0.0", "reason": "Please use Deduce().deidentify(text) instead."}


@deprecated.deprecated(**deprecation_info)
def annotate_text(*args, **kwargs) -> Any:
    return deduce.backwards_compat.annotate_text_backwardscompat(*args, **kwargs)


@deprecated.deprecated(**deprecation_info)
def annotate_text_structured(*args, **kwargs) -> Any:
    return deduce.backwards_compat.annotate_text_structured_backwardscompat(*args, **kwargs)


@deprecated.deprecated(**deprecation_info)
def deidentify_annotations(*args, **kwargs) -> Any:
    return deduce.backwards_compat.deidentify_annotations_backwardscompat(*args, **kwargs)
