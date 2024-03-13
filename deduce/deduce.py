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
from frozendict import frozendict

from deduce import utils
from deduce.lookup_struct_loader import load_interfix_lookup, load_prefix_lookup
from deduce.lookup_structs import get_lookup_structs, load_raw_itemsets
from deduce.processor_loader import DeduceProcessorLoader
from deduce.tokenizer import DeduceTokenizer

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
        looup_data_path: The path to look for lookup data, by default included in
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

        self.lookup_data_path = self._initialize_lookup_data_path(lookup_data_path)
        self.tokenizers = {"default": self._initialize_tokenizer(self.lookup_data_path)}

        self.lookup_structs = get_lookup_structs(
            lookup_path=self.lookup_data_path,
            tokenizer=self.tokenizers["default"],
            deduce_version=__version__,
            build=build_lookup_structs,
        )

        self.annotator_load_extras = {
            "tokenizer": self.tokenizers["default"],
            "ds": self.lookup_structs,
            "use_recall_boost": self.config["use_recall_boost"],
        }

        self.annotator_loader = DeduceProcessorLoader()
        self.processors = self.annotator_loader.load(
            config=self.config, extras=self.annotator_load_extras
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
