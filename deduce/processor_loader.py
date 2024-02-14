from typing import Optional

import docdeid as dd
from deprecated import deprecated
from frozendict import frozendict

from deduce import utils
from deduce.annotation_processor import (
    CleanAnnotationTag,
    DeduceMergeAdjacentAnnotations,
    PersonAnnotationConverter,
    RemoveAnnotations,
)
from deduce.annotator import ContextAnnotator, TokenPatternAnnotator
from deduce.redactor import DeduceRedactor


class DeduceProcessorLoader:  # pylint: disable=R0903
    """Responsible for loading all processors that Deduce should use, based on config
    and deduce logic."""

    @staticmethod
    def _get_multi_token_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        lookup_struct = extras["ds"][args["lookup_values"]]

        if isinstance(lookup_struct, dd.ds.LookupSet):
            args.update(
                lookup_values=lookup_struct.items(),
                matching_pipeline=lookup_struct.matching_pipeline,
                tokenizer=extras["tokenizer]"],
            )
        elif isinstance(lookup_struct, dd.ds.LookupTrie):
            args.update(trie=lookup_struct)
            del args["lookup_values"]
        else:
            raise ValueError(
                f"Don't know how to present lookup structure with type "
                f"{type(lookup_struct)} to MultiTokenLookupAnnotator"
            )
        DeduceProcessorLoader._handle_recall_booster(extras, args)

        return dd.process.MultiTokenLookupAnnotator(**args)

    @deprecated(
        "The multi_token annotatortype is deprecated and will be removed in a "
        "future version. Please set annotator_type field to "
        "docdeid.process.MultiTokenAnnotator. See "
        "https://github.com/vmenger/deduce/blob/main/base_config.json for examples."
    )
    def _get_multi_token_annotator_old(self, *args, **kwargs) -> dd.process.Annotator:
        return self._get_multi_token_annotator(*args, **kwargs)

    @staticmethod
    @deprecated(
        "The token_pattern annotatortype is deprecated and will be removed in "
        "a future version. Please set annotator_type field to "
        "deduce.annotator.TokenPatternAnnotator. See "
        "https://github.com/vmenger/deduce/blob/main/base_config.json for "
        "examples."
    )
    def _get_token_pattern_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        return TokenPatternAnnotator(**args, ds=extras["ds"])

    @staticmethod
    @deprecated(
        "The dd_token_pattern annotatortype is deprecated and will be removed "
        "in a future version. For patient name patterns, please use "
        "deduce.annotator.PatientNameAnnotator. For other patterns, please "
        "switch to deduce.annotator.TokenPatternAnnotator. See "
        "https://github.com/vmenger/deduce/blob/main/base_config.json for "
        "examples."
    )
    def _get_dd_token_pattern_annotator(
        args: dict, extras: dict
    ) -> dd.process.Annotator:
        pattern_args = args.pop("pattern")
        module = pattern_args.pop("module")
        cls = pattern_args.pop("class")
        cls = utils.get_class_from_name(module, cls)

        pattern = utils.initialize_class(cls, args=pattern_args, extras=extras)

        return dd.process.TokenPatternAnnotator(pattern=pattern)

    @staticmethod
    @deprecated(
        "The annotation_context annotatortype is deprecated and will be "
        "removed in a future version. Please set annotator_type field to "
        "deduce.annotator.ContextAnnotator. See "
        "https://github.com/vmenger/deduce/blob/main/base_config.json for "
        "examples."
    )
    def _get_context_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        return ContextAnnotator(**args, ds=extras["ds"])

    @staticmethod
    @deprecated(
        "The custom annotatortype is deprecated and will be removed in a "
        "future version. Please set annotator_type field to module.class "
        "directly, and remove module and class from args. See "
        "https://github.com/vmenger/deduce/blob/main/base_config.json for "
        "examples."
    )
    def _get_custom_annotator(args: dict, extras: dict) -> dd.process.Annotator:
        module = args.pop("module")
        cls = args.pop("class")

        cls = utils.get_class_from_name(module, cls)
        return utils.initialize_class(cls, args=args, extras=extras)

    @staticmethod
    @deprecated(
        "The regexp annotatortype is deprecated and will be removed in a future "
        "version. Please set annotator_type field to "
        "deduce.annotator.ContextAnnotator. See "
        "https://github.com/vmenger/deduce/blob/main/base_config.json for "
        "examples.",
    )
    def _get_regexp_annotator(
        args: dict,
        extras: dict,  # pylint: disable=W0613
    ) -> dd.process.Annotator:
        DeduceProcessorLoader._handle_recall_booster(extras, args)
        return dd.process.RegexpAnnotator(**args)

    @staticmethod
    def _add_recall_booster_arguments(
        recall_boost_config: dict, processor_args: dict
    ) -> None:
        """Adds recall booster arguments to processor arguments."""
        recall_boost_type = recall_boost_config["recall_boost_type"]
        if recall_boost_type.endswith("MinimumLengthExpander"):
            str_processors = recall_boost_config["args"]["str_processors"]
            str_processors = [utils.get_class_from_string(p)() for p in str_processors]
            expander = utils.get_class_from_string(recall_boost_type)
            expander = expander(
                str_processors,
                min_length=recall_boost_config["args"]["min_len"],
            )
            processor_args["expander"] = expander
        elif recall_boost_type == "argument_replacement":
            for key, value in recall_boost_config["args"].items():
                if key not in processor_args:
                    raise ValueError(
                        "argument_replacement is only possible \
                        for args that exist in processor arguments"
                    )
                processor_args[key] = value
        else:
            raise ValueError(
                f"Unknown recall boost type {recall_boost_config['recall_boost_type']}"
            )

    @staticmethod
    def _handle_recall_booster(extras: dict, processor_args: dict) -> None:
        """
        Checks if recall boost is turned on in config and annotator has a recall boost
        config.

        If so, adds recall booster arguments to processor args.
        """
        # if recall boost config available for this annotator
        if "recall_boost_config" in processor_args:
            # if recall boost should be used according to config
            if extras.get("use_recall_boost"):
                # instantiate recall boost
                recall_boost_config = processor_args["recall_boost_config"]
                DeduceProcessorLoader._add_recall_booster_arguments(
                    recall_boost_config, processor_args
                )
            del processor_args["recall_boost_config"]

    @staticmethod
    def _get_annotator_from_class(
        annotator_type: str, args: dict, extras: dict
    ) -> dd.process.Annotator:
        cls = utils.get_class_from_string(annotator_type)
        DeduceProcessorLoader._handle_recall_booster(extras, args)
        return utils.initialize_class(cls, args, extras)

    @staticmethod
    def _get_or_create_annotator_group(
        group_name: Optional[str], processors: dd.process.DocProcessorGroup
    ) -> dd.process.DocProcessorGroup:
        if group_name is None:
            group = processors  # top level
        elif group_name in processors.get_names(recursive=False):
            existing_group = processors[group_name]

            if not isinstance(existing_group, dd.process.DocProcessorGroup):
                raise RuntimeError(
                    f"processor with name {group_name} already exists, "
                    f"but is no group"
                )

            group = existing_group

        else:
            group = dd.process.DocProcessorGroup()
            processors.add_processor(group_name, group)

        return group

    def _load_annotators(
        self, config: frozendict, extras: dict
    ) -> dd.process.DocProcessorGroup:
        annotator_creators = {
            "docdeid.process.MultiTokenLookupAnnotator": self._get_multi_token_annotator,  # noqa: E501, pylint: disable=C0301
            "multi_token": self._get_multi_token_annotator_old,
            "token_pattern": self._get_token_pattern_annotator,
            "dd_token_pattern": self._get_dd_token_pattern_annotator,
            "annotation_context": self._get_context_annotator,
            "regexp": self._get_regexp_annotator,
            "custom": self._get_custom_annotator,
        }

        annotators = dd.process.DocProcessorGroup()

        for annotator_name, annotator_info in config.items():
            group = self._get_or_create_annotator_group(
                annotator_info.get("group", None), processors=annotators
            )

            annotator_type = annotator_info["annotator_type"]
            args = annotator_info["args"]

            if annotator_type in annotator_creators:
                annotator = annotator_creators[annotator_type](args, extras)
            else:
                annotator = self._get_annotator_from_class(annotator_type, args, extras)

            group.add_processor(annotator_name, annotator)

        return annotators

    @staticmethod
    def _load_name_processors(name_group: dd.process.DocProcessorGroup) -> None:
        name_group.add_processor(
            "person_annotation_converter", PersonAnnotationConverter()
        )

    @staticmethod
    def _load_location_processors(location_group: dd.process.DocProcessorGroup) -> None:
        location_group.add_processor(
            "remove_street_tags", RemoveAnnotations(tags=["straat"])
        )

        location_group.add_processor(
            "clean_street_tags",
            CleanAnnotationTag(
                tag_map={
                    "straat+huisnummer": "locatie",
                    "straat+huisnummer+huisnummerletter": "locatie",
                }
            ),
        )

    @staticmethod
    def _load_post_processors(
        config: frozendict, post_group: dd.process.DocProcessorGroup
    ) -> None:
        """TODO."""

        sort_by_attrs = config["resolve_overlap_strategy"]["attributes"]
        sort_by_ascending = config["resolve_overlap_strategy"]["ascending"]

        sort_by = []
        sort_by_callbacks = {}

        for attr, ascending in zip(sort_by_attrs, sort_by_ascending):
            sort_by.append(attr)
            sort_by_callbacks[attr] = (lambda x: x) if ascending else (lambda y: -y)

        post_group.add_processor(
            "overlap_resolver",
            dd.process.OverlapResolver(
                sort_by=tuple(sort_by), sort_by_callbacks=frozendict(sort_by_callbacks)
            ),
        )

        post_group.add_processor(
            "merge_adjacent_annotations",
            DeduceMergeAdjacentAnnotations(
                slack_regexp=config["adjacent_annotations_slack"], check_overlap=False
            ),
        )

        post_group.add_processor(
            "redactor",
            DeduceRedactor(
                open_char=config["redactor_open_char"],
                close_char=config["redactor_close_char"],
            ),
        )

    def load(self, config: frozendict, extras: dict) -> dd.process.DocProcessorGroup:
        """
        Loads all processors. Loads annotators from config, and then adds document
        processors based on logic that is internal to the Deduce class.

        Args:
            config: The config.
            extras: Any extras that should be passed to annotators/annotation processors
            as keyword arguments, e.g. tokenizers or datastructures.

        Returns:
            A docprocessorgroup containing all annotators/processors.
        """

        processors = self._load_annotators(config=config["annotators"], extras=extras)

        self._load_name_processors(
            name_group=self._get_or_create_annotator_group(
                group_name="names", processors=processors
            )
        )

        self._load_location_processors(
            location_group=self._get_or_create_annotator_group(
                group_name="locations", processors=processors
            )
        )

        post_group = dd.process.DocProcessorGroup()
        processors.add_processor("post_processing", post_group)

        self._load_post_processors(config=config, post_group=post_group)

        return processors
