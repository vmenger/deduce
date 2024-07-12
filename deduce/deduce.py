"""Loads Deduce and all its components."""

import importlib.metadata
import itertools
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional, Union

import docdeid as dd
from deprecated import deprecated

from docdeid.ds import LookupSet, LookupTrie
from frozendict import frozendict

from deduce import utils
from deduce.annotation_processor import (
    CleanAnnotationTag,
    DeduceMergeAdjacentAnnotations,
    PersonAnnotationConverter,
    RemoveAnnotations,
)
from deduce.lookup_struct_loader import load_interfix_lookup, load_prefix_lookup
from deduce.lookup_structs import get_lookup_structs, load_raw_itemsets
from deduce.redactor import DeduceRedactor
from deduce.tokenizer import DeduceTokenizer

__version__ = importlib.metadata.version(__package__ or __name__)


from deduce.utils import ensure_path

_BASE_PATH = Path(os.path.dirname(__file__)).parent
_LOOKUP_LIST_PATH = _BASE_PATH / "deduce" / "data" / "lookup"
_BASE_CONFIG_FILE = _BASE_PATH / "base_config.json"


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class Deduce(dd.DocDeid):  # pylint: disable=R0903
    """
    Main class for de-identification.

    Inherits from ``docdeid.DocDeid``, and as such, most information on deidentifying
    text with a Deduce object is available there.

    Args:
        load_base_config: Whether or not to load the base config that is packaged with
            deduce. This loads some sensible defaults, although further customization
            is always recommended.
        config: A specific user config, either as a dict, or pointing to a `json` file.
            When `load_base_config` is set to `True`, only settings defined in `config`
            are overwritten, and other defaults are kept. When `load_base_config` is
            set to `False`, no defaults are loaded and only configuration from `config`
            is applied.
        lookup_data_path: The path to look for lookup data, by default included in
            the package. If you want to make changes to source files, it's recommended
            to copy the source data and pointing deduce to this folder with this
            argument.
        build_lookup_structs: Will always reload and rebuild lookup structs
            rather than using the cache when this is set to `True`.
        save_lookup_structs: Should the lookup structures be pickled (cached)
            upon loading? Default: `True`.
    """

    def __init__(  # pylint: disable=R0913
        self,
        load_base_config: bool = True,
        config: Optional[Union[str, dict]] = None,
        config_file: Optional[str] = None,
        lookup_data_path: Union[str, Path] = _LOOKUP_LIST_PATH,
        build_lookup_structs: bool = False,
        save_lookup_structs: bool = True,
    ) -> None:

        super().__init__()

        if config_file is not None:

            warnings.warn(
                "The config_file keyword is deprecated, please use config "
                "instead, which accepts both filenames and dictionaries.",
                DeprecationWarning,
            )

            config = config_file

        logging.info("Going to init config.")
        self.config = self._initialize_config(
            load_base_config=load_base_config, user_config=config
        )

        self.lookup_data_path = ensure_path(lookup_data_path)

        logging.info("Going to init tokenizers.")
        self.tokenizers = {"default": self._initialize_tokenizer(self.lookup_data_path)}
        logging.debug("Done initing tokenizers.")

        self.lookup_structs = get_lookup_structs(
            lookup_path=self.lookup_data_path,
            tokenizer=self.tokenizers["default"],
            deduce_version=__version__,
            build=build_lookup_structs,
            save_cache=save_lookup_structs,
        )
        logging.info("Done loading lookup structs.")

        extras = {"tokenizer": self.tokenizers["default"], "ds": self.lookup_structs}

        logging.info("Going to load the Deduce processor.")
        self.processors = _DeduceProcessorLoader().load(
            config=self.config, extras=extras
        )

    @staticmethod
    def _initialize_config(
        load_base_config: bool = True,
        user_config: Optional[Union[str, dict]] = None,
    ) -> frozendict:
        """
        Initialize the configuration.

        Returns:
            The config as a dictionary, based provided input file and default logic.
        """

        config: dict[str, Any] = {}

        if load_base_config:

            with open(_BASE_CONFIG_FILE, "r", encoding="utf-8") as file:
                base_config = json.load(file)

            utils.overwrite_dict(config, base_config)

        if user_config is not None:
            if isinstance(user_config, str):
                with open(user_config, "r", encoding="utf-8") as file:
                    user_config = json.load(file)

            utils.overwrite_dict(config, user_config)

        return frozendict(config)

    @staticmethod
    def _initialize_tokenizer(lookup_data_path: Path) -> dd.Tokenizer:

        raw_itemsets = load_raw_itemsets(
            base_path=lookup_data_path,
            subdirs=["names/lst_interfix", "names/lst_prefix"],
        )

        prefix = load_prefix_lookup(raw_itemsets)
        interfix = load_interfix_lookup(raw_itemsets)

        merge_terms = itertools.chain(prefix.items(), interfix.items())

        return DeduceTokenizer(merge_terms=merge_terms)


class _DeduceProcessorLoader:  # pylint: disable=R0903
    """Responsible for loading all processors that Deduce should use, based on config
    and deduce logic."""

    @staticmethod
    def _get_multi_token_annotator(args: dict, extras: dict) -> dd.process.Annotator:

        lookup_struct = extras["ds"][args.pop("lookup_values")]

        if isinstance(lookup_struct, LookupTrie):
            lookup_trie = lookup_struct
        elif isinstance(lookup_struct, LookupSet):
            try:
                tokenizer = args["tokenizer"]
            except KeyError:
                # This indicates an error in the code, not in configuration, as
                # the "tokenizer" key is always added to `extras` where `extras` is
                # defined -- in `Deduce.__init__`.
                # pylint: disable=W0707
                raise ValueError(
                    "When constructing a MultiTokenLookupAnnotator from a LookupSet, "
                    "a tokenizer must be given."
                )

            lookup_trie = LookupTrie(matching_pipeline=lookup_struct.matching_pipeline)
            for phrase in filter(None, map(tokenizer.tokenize, lookup_struct)):
                lookup_trie.add_item([token.text for token in phrase])
        else:
            raise ValueError(
                f"Don't know how to present lookup structure with type "
                f"{type(lookup_struct)} to MultiTokenLookupAnnotator"
            )

        return dd.process.MultiTokenLookupAnnotator(trie=lookup_trie, **args)

    @staticmethod
    def _get_annotator_from_class(
        annotator_type: str, args: dict, extras: dict
    ) -> dd.process.Annotator:

        elems = annotator_type.split(".")
        module_name = ".".join(elems[:-1])
        class_name = elems[-1]

        cls = utils.class_for_name(module_name=module_name, class_name=class_name)

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
            "patient_cleaner",
            CleanAnnotationTag(
                tag_map={
                    "voornaam_patient": "patient",
                    "initiaal_patient": "patient",
                    "achternaam_patient": "patient",
                    "part_of_patient": "persoon",
                    # TODO We should probably merge this new "person"
                    #  annotation with neighbouring annotations in yet another
                    #  postprocessing step.
                }
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
        processors based on logic that is internal to this class.

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
