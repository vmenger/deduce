from docdeid.process.annotator import MultiTokenLookupAnnotator

from deduce.deduce import Deduce
from deduce.processor_loader import DeduceProcessorLoader
from deduce.str.processor import TitleCase


class TestDeduceUtils:
    def test_deduce_class_loader(self):
        expansion_str_modifiers = [TitleCase()]
        recall_boost_type = "docdeid.str.expander.MinimumLengthExpander"
        expander = DeduceProcessorLoader._get_class_from_string(recall_boost_type)
        expander = expander(expansion_str_modifiers, min_length=4)
        expansions = expander.expand_item("expansion test")
        assert expansions == {"expansion test", "Expansion Test"}

    def test_recall_booster_in_config(self):
        base_config = dict(Deduce._initialize_config())
        base_config["use_recall_boost"] = True
        # remove annotators that do not have a recall boost config
        base_config["annotators"] = {
            ann_key: ann_value
            for ann_key, ann_value in base_config["annotators"].items()
            if "recall_boost_config" in ann_value["args"]
        }
        config_annotator_names = set(base_config["annotators"].keys())
        real_deduce = Deduce(load_base_config=False, config=base_config)

        processor_names, processors = zip(
            *((n, p) for n, p in real_deduce.processors.iter_doc_processors() if p)
        )
        assert all(
            config_name in processor_names for config_name in config_annotator_names
        )
        for processor in processors:
            if isinstance(processor, MultiTokenLookupAnnotator):
                assert processor.expander is not None

        # lowercased version of a first name in text would not be detected without recall boost
        result = real_deduce.deidentify("Mijn naam is lydia")
        assert result.deidentified_text == "Mijn naam is [PERSOON-1]"
        # test minimum length requirement
        result = real_deduce.deidentify("Mijn naam is jos")
        assert result.deidentified_text == "Mijn naam is jos"

        # test for lowercase lastname removal
        result = real_deduce.deidentify("Mijn achternaam is vaarkamp")
        assert result.deidentified_text == "Mijn achternaam is [PERSOON-1]"
        # test minimum length requirement
        result = real_deduce.deidentify("Mijn achternaam is vu")
        assert result.deidentified_text == "Mijn achternaam is vu"
