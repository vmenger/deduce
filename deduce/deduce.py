import json
import os
import re
import warnings
from pathlib import Path
from typing import Any, Optional

import deprecated
import docdeid as dd

import deduce.backwards_compat
from deduce import utils
from deduce.lookup_sets import get_lookup_sets
from deduce.process.annotation_processing import (
    DeduceMergeAdjacentAnnotations,
    PersonAnnotationConverter,
)
from deduce.process.annotator import AnnotationContextPatternAnnotator
from deduce.process.redact import DeduceRedactor
from deduce.tokenize import DeduceTokenizer

warnings.simplefilter(action="once")


class Deduce(dd.DocDeid):
    """
    Main class for de-identifiation.

    Inherits from ``docdeid.DocDeid``, and as such, most information is available in the documentation there.
    """

    def __init__(self, config_file: Optional[str] = None) -> None:
        super().__init__()

        self.config = self._initialize_config(config_file)
        self.lookup_sets = get_lookup_sets()
        self.tokenizers = self._initialize_tokenizers()
        self.initialize_doc_processors()

    @staticmethod
    def _initialize_config(config_file: Optional[str] = None) -> dict:
        """
        Initialize the config file.

        Args:
            config_file: The filepath of the config file.

        Returns:
            The contents of the config file as a dictionary.
        """

        config_path = Path(config_file) if config_file else Path(os.path.dirname(__file__)).parent / "config.json"

        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _initialize_tokenizers(self) -> dict:
        """Initializes tokenizers."""

        merge_terms = dd.ds.LookupSet()
        merge_terms.add_items_from_iterable(["A1", "A2", "A3", "A4", "\n", "\r", "\t"])
        merge_terms += self.lookup_sets["interfixes"]
        merge_terms += self.lookup_sets["prefixes"]

        return {"default": DeduceTokenizer(merge_terms=merge_terms)}

    @staticmethod
    def _initialize_annotators(
        annotator_cnfg: dict, lookup_sets: dd.ds.DsCollection, tokenizer: dd.tokenize.Tokenizer
    ) -> dd.process.DocProcessorGroup:
        """Initializes annotators."""

        extras = {"lookup_sets": lookup_sets, "tokenizer": tokenizer}
        return _AnnotatorFactory().get_annotators(annotator_cnfg, extras)

    def initialize_doc_processors(self) -> None:
        """
        Initializes document processors.

        Need to re-run this when updating lookup sets.
        """

        config = self.config.copy()  # copy to prevent accidental overwrites, deletes, etc

        self.processors = self._initialize_annotators(
            config["annotators"].copy(), self.lookup_sets, self.tokenizers["default"]
        )
        self.processors["names"].add_processor("person_annotation_converter", PersonAnnotationConverter())

        sort_by_attr = self.config["resolve_overlap_strategy"]["attribute"]
        sort_by = [sort_by_attr]
        sort_by_callbacks = (
            {sort_by_attr: lambda x: -x} if not config["resolve_overlap_strategy"]["ascending"] else None
        )

        post_group = dd.process.DocProcessorGroup()
        self.processors.add_processor("post_processing", post_group)

        post_group.add_processor(
            "overlap_resolver",
            dd.process.OverlapResolver(sort_by=sort_by, sort_by_callbacks=sort_by_callbacks),
        )

        post_group.add_processor(
            "merge_adjacent_annotations",
            DeduceMergeAdjacentAnnotations(slack_regexp=config["adjacent_annotations_slack"]),
        )

        post_group.add_processor(
            "redactor",
            DeduceRedactor(open_char=config["redactor_open_char"], close_char=config["redactor_close_char"]),
        )


class _AnnotatorFactory:
    """Responsible for creating annotators, based on config."""

    def __init__(self) -> None:
        self.annotator_creators = {
            "token_pattern": self._get_token_pattern_annotator,
            "annotation_context": self._get_annotation_context_pattern_annotator,
            "regexp": self._get_regexp_annotator,
            "multi_token": self._get_multi_token_annotator,
        }

    @staticmethod
    def _get_token_pattern_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        pattern = utils.import_and_initialize(args.pop("pattern"), extras=extras)
        return dd.process.TokenPatternAnnotator(pattern=pattern)

    @staticmethod
    def _get_annotation_context_pattern_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        context_patterns = [utils.import_and_initialize(p["pattern"], extras=extras) for p in args.pop("patterns")]
        return AnnotationContextPatternAnnotator(context_patterns=context_patterns, **args)

    @staticmethod
    def _get_regexp_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        args["regexp_pattern"] = re.compile(args["regexp_pattern"])
        return dd.process.RegexpAnnotator(**args)

    @staticmethod
    def _get_multi_token_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        if isinstance(args["lookup_values"], str):
            lookup_set = extras["lookup_sets"][args["lookup_values"]]

            args["lookup_values"] = lookup_set.items()
            args["matching_pipeline"] = lookup_set.matching_pipeline

        args["tokenizer"] = DeduceTokenizer()

        return dd.process.MultiTokenLookupAnnotator(**args)

    def get_annotators(self, annotator_cnfg: dict, extras: dict) -> dd.process.DocProcessorGroup:
        """
        Get the annotators, requested in the annotator config.

        Args:
            annotator_cnfg: A dictionary containing configuration on which annotators to initialize.
            extras: Any additional objects passed to pattern or annotator init, if present

        Returns:
            A DocProcessorGroup containing the initialized annotators specified in the config dict.
        """

        annotators = dd.process.DocProcessorGroup()

        for annotator_name, annotator_info in annotator_cnfg.items():

            if annotator_info["annotator_type"] not in self.annotator_creators:
                raise ValueError(f"Unexpected annotator_type {annotator_info['annotator_type']}")

            group = annotators

            if "group" in annotator_info:

                if annotator_info["group"] not in annotators.get_names(recursive=False):
                    annotators.add_processor(annotator_info["group"], dd.process.DocProcessorGroup())

                group = annotators[annotator_info["group"]]

            annotator = self.annotator_creators[annotator_info["annotator_type"]](annotator_info["args"], extras)
            group.add_processor(annotator_name, annotator)

        return annotators


# Backwards compatibility stuff beneath this line.
deduce.backwards_compat._BackwardsCompat.set_deduce_model(Deduce())
deprecation_info = {
    "version": "2.0.0",
    "reason": "Please use Deduce().deidentify(text) instead. "
    "See: https://deduce.readthedocs.io/en/latest/migrating.html",
}


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
