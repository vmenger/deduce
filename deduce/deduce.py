import json
import os
import re
from pathlib import Path
from typing import Optional

import docdeid as dd

from deduce import utils
from deduce.annotation_processing import (
    CleanAnnotationTag,
    DeduceMergeAdjacentAnnotations,
    PersonAnnotationConverter,
    RemoveAnnotations,
)
from deduce.annotator import ContextAnnotator, TokenPatternAnnotator
from deduce.lookup_sets import get_lookup_sets
from deduce.redact import DeduceRedactor
from deduce.tokenizer import DeduceTokenizer


class Deduce(dd.DocDeid):
    """
    Main class for de-identifiation.

    Inherits from ``docdeid.DocDeid``, and as such, most information is available
    in the documentation there.
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        use_config_defaults: Optional[bool] = True,
    ) -> None:
        super().__init__()

        self.config_file = config_file
        self.use_config_defaults = use_config_defaults

        self.config = self._initialize_config()

        self.lookup_sets = get_lookup_sets()
        self.tokenizers = self._initialize_tokenizers()
        self.initialize_doc_processors()

    def _initialize_config(self) -> dict:
        """
        Initialize the config file.

        Returns:
            The config as a dictionary, based provided input file and default logic.
        """

        if self.config_file is None and not self.use_config_defaults:
            raise ValueError(
                "Please specify a config file, or set use_config_defaults to True"
            )

        default_config_path = Path(os.path.dirname(__file__)).parent / "config.json"

        if self.use_config_defaults:
            with open(default_config_path, "r", encoding="utf-8") as file:
                config = json.load(file)

        if self.config_file is not None:
            with open(Path(self.config_file), "r", encoding="utf-8") as file:
                custom_config = json.load(file)

            config = utils.overwrite_dict(config, custom_config)

        return config

    def _initialize_tokenizers(self) -> dict:
        """Initializes tokenizers."""

        merge_terms = dd.ds.LookupSet()
        merge_terms += self.lookup_sets["interfixes"]
        merge_terms += self.lookup_sets["prefixes"]

        return {"default": DeduceTokenizer(merge_terms=merge_terms)}

    @staticmethod
    def _initialize_annotators(
        annotator_cnfg: dict,
        lookup_sets: dd.ds.DsCollection,
        tokenizer: dd.tokenize.Tokenizer,
    ) -> dd.process.DocProcessorGroup:
        """Initializes annotators."""

        extras = {"ds": lookup_sets, "lookup_sets": lookup_sets, "tokenizer": tokenizer}
        return _AnnotatorFactory().get_annotators(annotator_cnfg, extras)

    def initialize_doc_processors(self) -> None:
        """
        Initializes document processors.

        Need to re-run this when updating lookup sets.
        """

        config = (
            self.config.copy()
        )  # copy to prevent accidental overwrites, deletes, etc

        self.processors = self._initialize_annotators(
            config["annotators"].copy(), self.lookup_sets, self.tokenizers["default"]
        )
        self.processors["names"].add_processor(
            "person_annotation_converter", PersonAnnotationConverter()
        )

        self.processors["locations"].add_processor(
            "remove_street_tags", RemoveAnnotations(tags=["straat"])
        )

        self.processors["locations"].add_processor(
            "clean_street_tags",
            CleanAnnotationTag(
                tag_map={
                    "straat+huisnummer": "locatie",
                    "straat+huisnummer+huisnummerletter": "locatie",
                }
            ),
        )

        sort_by_attrs = self.config["resolve_overlap_strategy"]["attributes"]
        sort_by_ascending = self.config["resolve_overlap_strategy"]["ascending"]

        sort_by = []
        sort_by_callbacks = {}

        for attr, ascending in zip(sort_by_attrs, sort_by_ascending):
            sort_by.append(attr)
            sort_by_callbacks[attr] = (lambda x: x) if ascending else (lambda y: -y)

        post_group = dd.process.DocProcessorGroup()
        self.processors.add_processor("post_processing", post_group)

        post_group.add_processor(
            "overlap_resolver",
            dd.process.OverlapResolver(
                sort_by=sort_by, sort_by_callbacks=sort_by_callbacks
            ),
        )

        post_group.add_processor(
            "merge_adjacent_annotations",
            DeduceMergeAdjacentAnnotations(
                slack_regexp=config["adjacent_annotations_slack"]
            ),
        )

        post_group.add_processor(
            "redactor",
            DeduceRedactor(
                open_char=config["redactor_open_char"],
                close_char=config["redactor_close_char"],
            ),
        )


class _AnnotatorFactory:  # pylint: disable=R0903
    """Responsible for creating annotators, based on config."""

    def __init__(self) -> None:
        self.annotator_creators = {
            "token_pattern": self._get_token_pattern_annotator,
            "dd_token_pattern": self._get_dd_token_pattern_annotator,
            "annotation_context": self._get_context_annotator,
            "regexp": self._get_regexp_annotator,
            "multi_token": self._get_multi_token_annotator,
            "custom": self._get_custom_annotator,
        }

    @staticmethod
    def _get_token_pattern_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        return TokenPatternAnnotator(**args, ds=extras["ds"])

    @staticmethod
    def _get_dd_token_pattern_annotator(
        args: dict, extras: dict
    ) -> dd.process.Annotator:
        pattern = utils.import_and_initialize(args.pop("pattern"), extras=extras)
        return dd.process.TokenPatternAnnotator(pattern=pattern)

    @staticmethod
    def _get_context_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        return ContextAnnotator(**args, ds=extras["ds"])

    @staticmethod
    def _get_regexp_annotator(
        args: dict, extras: dict  # pylint: disable=W0613
    ) -> dd.process.Annotator:
        args["regexp_pattern"] = re.compile(args["regexp_pattern"])
        return dd.process.RegexpAnnotator(**args)

    @staticmethod
    def _get_multi_token_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        if isinstance(args["lookup_values"], str):
            lookup_set = extras["lookup_sets"][args["lookup_values"]]

            args["lookup_values"] = lookup_set.items()
            args["matching_pipeline"] = lookup_set.matching_pipeline

        return dd.process.MultiTokenLookupAnnotator(
            **args, tokenizer=extras["tokenizer"]
        )

    @staticmethod
    def _get_custom_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        return utils.import_and_initialize(args=args, extras=extras)

    def get_annotators(
        self, annotator_cnfg: dict, extras: dict
    ) -> dd.process.DocProcessorGroup:
        """
        Get the annotators, requested in the annotator config.

        Args:
            annotator_cnfg: A dictionary containing configuration on which annotators
            to initialize.
            extras: Any additional objects passed to pattern or annotator init,
            if present.

        Returns:
            A DocProcessorGroup containing the initialized annotators specified
            in the config dict.
        """

        annotators = dd.process.DocProcessorGroup()

        for annotator_name, annotator_info in annotator_cnfg.items():
            if annotator_info["annotator_type"] not in self.annotator_creators:
                raise ValueError(
                    f"Unexpected annotator_type {annotator_info['annotator_type']}"
                )

            group = annotators

            if "group" in annotator_info:
                if annotator_info["group"] not in annotators.get_names(recursive=False):
                    annotators.add_processor(
                        annotator_info["group"], dd.process.DocProcessorGroup()
                    )

                group = annotators[annotator_info["group"]]

            annotator = self.annotator_creators[annotator_info["annotator_type"]](
                annotator_info["args"], extras
            )
            group.add_processor(annotator_name, annotator)

        return annotators
