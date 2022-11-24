import warnings
from typing import Any, Optional

import deprecated
import docdeid as dd

import deduce.backwards_compat
from deduce.lookup_sets import get_lookup_sets
from deduce.process.annotation_processing import DeduceMergeAdjacentAnnotations
from deduce.process.redact import DeduceRedactor
from deduce.tokenize import DeduceTokenizer
import deduce.utils

import re

from pathlib import Path
import deduce.utils
from deduce.process.annotation_processing import PersonAnnotationConverter
from deduce.process.annotator import AnnotationContextPatternAnnotator


import json
import os


warnings.simplefilter(action="once")


class Deduce(dd.DocDeid):
    """
    Main class for de-identifiation.

    Inherits from ``docdeid.DocDeid``, and as such, most information is available in the documentation there.
    """

    def __init__(self) -> None:
        super().__init__()
        self.config = read_config()
        self.lookup_sets = get_lookup_sets()
        self._initialize_deduce()

    def _initialize_tokenizer(self) -> None:
        """Initializes tokenizer."""

        merge_terms = dd.ds.LookupSet()
        merge_terms.add_items_from_iterable(["A1", "A2", "A3", "A4", "\n", "\r", "\t"])
        merge_terms += self.lookup_sets["interfixes"]
        merge_terms += self.lookup_sets["prefixes"]

        self.tokenizers["default"] = DeduceTokenizer(merge_terms=merge_terms)

    def _initialize_processors(self) -> None:
        """Inializes document processors."""

        self.processors = get_doc_processors(self.config.copy(), self.lookup_sets, self.tokenizers["default"])

        self.processors.add_processor(
            "overlap_resolver",
            dd.process.OverlapResolver(sort_by=["length"], sort_by_callbacks={"length": lambda x: -x}),
        )

        self.processors.add_processor(
            "merge_adjacent_annotations", DeduceMergeAdjacentAnnotations(slack_regexp=r"[\.\s\-,]?[\.\s]?")
        )

        self.processors.add_processor("redactor", DeduceRedactor(open_char="<", close_char=">"))

    def _initialize_deduce(self) -> None:
        """Initialize."""

        self._initialize_tokenizer()
        self._initialize_processors()


def read_config(config_file: Optional[str] = None) -> dict:

    if config_file is None:
        config_file = Path(os.path.dirname(__file__)).parent / 'config.json'

    with open(config_file, 'r') as f:
        return json.load(f)


def _get_pattern(args: dict, extras: dict):

    cls = deduce.utils.class_for_name(args.pop("module"), args.pop("class"))

    for arg_name, arg in extras.items():
        if arg_name in cls.__init__.__code__.co_varnames:
            args[arg_name] = arg

    return cls(**args)


def _get_token_pattern_annotator(args: dict, extras: dict) -> dd.process.Annotator:

    pattern = _get_pattern(args.pop("pattern"), extras=extras)
    return dd.process.TokenPatternAnnotator(pattern=pattern)


def _get_annotation_context_pattern_annotator(args: dict, extras: dict) -> dd.process.Annotator:

    context_patterns = [_get_pattern(p['pattern'], extras=extras) for p in args.pop("patterns")]
    return AnnotationContextPatternAnnotator(context_patterns=context_patterns, **args)


def _get_regexp_annotator(args: dict, extras: dict) -> dd.process.Annotator:
    args['regexp_pattern'] = re.compile(args['regexp_pattern'])
    return dd.process.RegexpAnnotator(**args)


def _get_multi_token_annotator(args: dict, extras: dict) -> dd.process.Annotator:

    if isinstance(args['lookup_values'], str):
        lookup_set = extras['lookup_sets'][args['lookup_values']]

        args['lookup_values'] = lookup_set.items()
        args['matching_pipeline'] = lookup_set.matching_pipeline

    args['tokenizer'] = DeduceTokenizer()

    return dd.process.MultiTokenLookupAnnotator(**args)


ANNOTATOR_TYPE_TO_CREATOR = {
    "token_pattern": _get_token_pattern_annotator,
    "annotation_context": _get_annotation_context_pattern_annotator,
    "regexp": _get_regexp_annotator,
    "multi_token": _get_multi_token_annotator
}


def _get_annotators(annotator_cnfg: dict, lookup_sets: dd.ds.DsCollection, tokenizer: dd.Tokenizer) -> dd.process.DocProcessorGroup:
    extras = {"lookup_sets": lookup_sets, "tokenizer": tokenizer}
    annotators = dd.process.DocProcessorGroup()

    for annotator_name, annotator_info in annotator_cnfg.items():

        if annotator_info["annotator_type"] not in ANNOTATOR_TYPE_TO_CREATOR.keys():
            raise ValueError(f"Unexpected annotator_type {annotator_info['annotator_type']}")

        group = annotators

        if "group" in annotator_info:

            if annotator_info["group"] not in annotators.get_names(recursive=False):
                annotators.add_processor(annotator_info["group"], dd.process.DocProcessorGroup())

            group = annotators[annotator_info["group"]]

        annotator = ANNOTATOR_TYPE_TO_CREATOR[annotator_info["annotator_type"]](annotator_info["args"], extras)
        group.add_processor(annotator_name, annotator)

    return annotators


def get_doc_processors(cnfg: dict, lookup_sets: dd.ds.DsCollection, tokenizer: dd.Tokenizer) -> dd.process.DocProcessorGroup:

    annotators = _get_annotators(cnfg['annotators'], lookup_sets, tokenizer)
    annotators['names'].add_processor("person_annotation_converter", PersonAnnotationConverter())

    return annotators





# Backwards compatibility stuff beneath this line.
deduce.backwards_compat.BackwardsCompat.set_deduce_model(Deduce())
deprecation_info = {"version": "2.0.0", "reason": "Please use Deduce().deidentify(text) instead."}


@deprecated.deprecated(**deprecation_info)
def annotate_text(*args, **kwargs) -> Any:
    """Backwards compatibility function for annotating text."""
    return deduce.backwards_compat.annotate_text_backwardscompat(*args, **kwargs)


@deprecated.deprecated(**deprecation_info)
def annotate_text_structured(*args, **kwargs) -> Any:
    """Backwards compatibility function for annotating text structured."""
    return deduce.backwards_compat.annotate_text_structured_backwardscompat(*args, **kwargs)


@deprecated.deprecated(**deprecation_info)
def deidentify_annotations(*args, **kwargs) -> Any:
    """Backwards compatibility function for deidentifying annotations."""
    return deduce.backwards_compat.deidentify_annotations_backwardscompat(*args, **kwargs)
