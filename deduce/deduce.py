"""Loads Deduce and all its components."""

import importlib.metadata
import itertools
import json
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Optional, Union

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
from deduce.lookup_struct_loader import load_interfix_lookup, load_prefix_lookup
from deduce.lookup_structs import get_lookup_structs, load_raw_itemsets
from deduce.redactor import DeduceRedactor
from deduce.tokenizer import DeduceTokenizer
from deduce.data.lookup.src import all_lists

__version__ = importlib.metadata.version(__package__ or __name__)


_BASE_PATH = Path(os.path.dirname(__file__)).parent
_LOOKUP_LIST_PATH = _BASE_PATH / "deduce" / "data" / "lookup"
_BASE_CONFIG_FILE = _BASE_PATH / "base_config.json"


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
warnings.simplefilter(action="default")


class Deduce(dd.DocDeid):  # pylint: disable=R0903
    """
    Main class for de-identifiation.

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
        build_lookup_structs: Will always reload and rebuild lookup structs rather than
            using the cache when this is set to `True`.
    """

    def __init__(  # pylint: disable=R0913
        self,
        load_base_config: bool = True,
        config: Optional[Union[str, dict]] = None,
        config_file: Optional[str] = None,
        lookup_data_path: Union[str, Path] = _LOOKUP_LIST_PATH,
        build_lookup_structs: bool = False,
    ) -> None:

        global all_lists

        super().__init__()

        if config_file is not None:

            warnings.warn(
                "The config_file keyword is deprecated, please use config "
                "instead, which accepts both filenames and dictionaries.",
                DeprecationWarning,
            )

            config = config_file

        self.config = self._initialize_config(
            load_base_config=load_base_config, user_config=config
        )

        if "lookup_table_path" in self.config.keys():
            config_file_path = Path(os.path.dirname(Path(self.config["config_file_dir"])))
            self.lookup_data_path = config_file_path.joinpath(Path(self.config["lookup_table_path"]))
        else:
            self.lookup_data_path = Path(self._initialize_lookup_data_path(lookup_data_path))
        logging.info("Loading lookup data structures from: '" + str(self.lookup_data_path.absolute()) + "'.")
        self.tokenizers = {"default": self._initialize_tokenizer(self.lookup_data_path)}
        
        if "all_lists" in self.config.keys():
            all_lists=self.config["all_lists"]
        if len(all_lists) == 0:
            # generate a new one if deduce.data.lookup.src.all_lists is empty AND it is empty/not present in config.json
            all_lists=[]
            for i in self.lookup_data_path.glob("src/*/lst_*"):
                all_lists.append( os.path.basename(os.path.split(i)[0]) + "/" + os.path.basename(i))             
       
        self.lookup_structs = get_lookup_structs(
            lookup_path=Path(os.path.realpath(self.lookup_data_path)),
            tokenizer=self.tokenizers["default"],
            all_lists=all_lists,
            deduce_version=__version__,
            build=build_lookup_structs,
        )

        extras = {"tokenizer": self.tokenizers["default"], "ds": self.lookup_structs}

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
            # store the config-file-dir as an entry in the config dict
            config["config_file_dir"] = _BASE_CONFIG_FILE

        if user_config is not None:
            if isinstance(user_config, str):
                config["config_file_dir"] = user_config
                with open(user_config, "r", encoding="utf-8") as file:
                    user_config = json.load(file)

            utils.overwrite_dict(config, user_config)

        return frozendict(config)

    @staticmethod
    def _initialize_lookup_data_path(lookup_data_path: Union[str, Path]) -> Path:

        if isinstance(lookup_data_path, str):
            lookup_data_path = Path(lookup_data_path)

        return lookup_data_path

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

        lookup_struct = extras["ds"][args["lookup_values"]]

        if isinstance(lookup_struct, dd.ds.LookupSet):
            args.update(
                lookup_values=lookup_struct.items(),
                matching_pipeline=lookup_struct.matching_pipeline,
                tokenizer=extras["tokenizer"],
            )
        elif isinstance(lookup_struct, dd.ds.LookupTrie):
            args.update(trie=lookup_struct)
            del args["lookup_values"]
        else:
            raise ValueError(
                f"Don't know how to present lookup structure with type "
                f"{type(lookup_struct)} to MultiTokenLookupAnnotator"
            )

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
        cls = utils.class_for_name(module, cls)

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

        cls = utils.class_for_name(module, cls)
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
        args: dict, extras: dict  # pylint: disable=W0613
    ) -> dd.process.Annotator:

        return dd.process.RegexpAnnotator(**args)

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
