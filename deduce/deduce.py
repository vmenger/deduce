import warnings

import docdeid

from deduce.annotate.annotation_processing import DeduceMergeAdjacentAnnotations
from deduce.annotate.annotator import get_doc_processors
from deduce.annotate.redact import DeduceRedactor
from deduce.lookup.lookup_sets import get_lookup_sets
from deduce.tokenize.tokenizer import DeduceTokenizer

warnings.simplefilter(action="once")


class Deduce(docdeid.DocDeid):
    def __init__(self) -> None:
        super().__init__()
        self.lookup_sets = None
        self._initialize_deduce()

    def _initialize_lookup(self) -> None:
        self.lookup_sets = get_lookup_sets()

    def _initialize_tokenizer(self) -> None:

        merge_terms = docdeid.LookupSet()
        merge_terms.add_items_from_iterable(["A1", "A2", "A3", "A4", "\n", "\r", "\t"])
        merge_terms += self.lookup_sets["interfixes"]
        merge_terms += self.lookup_sets["prefixes"]

        self.tokenizers["default"] = DeduceTokenizer(merge_terms=merge_terms)

    def _initialize_processors(self) -> None:

        processors = get_doc_processors(self.lookup_sets, self.tokenizers["default"])

        for name, processor in processors.items():
            self.processors[name] = processor

        self.processors["overlap_resolver"] = docdeid.OverlapResolver(
            sort_by=["length"], sort_by_callbacks={"length": lambda x: -x}
        )

        self.processors["merge_adjacent_annotations"] = DeduceMergeAdjacentAnnotations(
            slack_regexp=r"[\.\s\-,]?[\.\s]?"
        )

        self.processors["redactor"] = DeduceRedactor()

    def _initialize_deduce(self) -> None:

        self._initialize_lookup()
        self._initialize_tokenizer()
        self._initialize_processors()


# Backwards compatibility stuff beneath this line.


def annotate_text(*args, **kwargs) -> str:

    warnings.warn(
        message="The annotate_text function will disappear in a future version. "
        "Please use Deduce().deidenitfy(text) instead.",
        category=DeprecationWarning,
    )

    from deduce.backwards_compat import annotate_text_backwardscompat

    return annotate_text_backwardscompat(*args, **kwargs)


def annotate_text_structured(*args, **kwargs) -> list[docdeid.Annotation]:

    warnings.warn(
        message="The annotate_text_structured function will disappear in a future version. "
        "Please use Deduce().deidenitfy(text) instead.",
        category=DeprecationWarning,
    )

    from deduce.backwards_compat import annotate_text_structured_backwardscompat

    return annotate_text_structured_backwardscompat(*args, **kwargs)


def deidentify_annotations(*args, **kwargs) -> str:

    warnings.warn(
        message="The deidentify_annotations function will disappear in a future version. "
        "Please use Deduce().deidenitfy(text) instead.",
        category=DeprecationWarning,
    )

    from deduce.backwards_compat import deidentify_annotations_backwardscompat

    return deidentify_annotations_backwardscompat(*args, **kwargs)
