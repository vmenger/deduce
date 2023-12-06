from pathlib import Path
from unittest.mock import patch

import docdeid as dd

from deduce.lookup_structs import (
    apply_transform,
    cache_lookup_structs,
    load_lookup_structs_from_cache,
    load_raw_itemset,
    load_raw_itemsets,
    validate_lookup_struct_cache,
)

DATA_PATH = Path(".").cwd() / "tests" / "data" / "lookup"


class TestLookupStruct:
    def test_apply_transform(self):

        items = {"den Burg", "Rotterdam"}
        transform = {"transforms": {"name": {"den": ["den", ""]}}}

        transformed_items = apply_transform(items, transform)

        assert transformed_items == {"den Burg", "Burg", "Rotterdam"}

    def test_apply_transform_no_strip_lines(self):

        items = {"den Burg", "Rotterdam"}
        transform = {"transforms": {"name": {"den": ["den", ""]}}, "strip_lines": False}

        transformed_items = apply_transform(items, transform)

        assert transformed_items == {"den Burg", " Burg", "Rotterdam"}

    def test_load_raw_itemset(self):

        raw_itemset = load_raw_itemset(DATA_PATH / "src" / "lst_test")

        assert len(raw_itemset) == 5
        assert "de Vries" in raw_itemset
        assert "De Vries" in raw_itemset
        assert "Sijbrand" in raw_itemset
        assert "Sybrand" in raw_itemset
        assert "Pieters" in raw_itemset
        assert "Wolter" not in raw_itemset

    def test_load_raw_itemset_nested(self):

        raw_itemset = load_raw_itemset(DATA_PATH / "src" / "lst_test_nested")

        assert raw_itemset == {"a", "b", "c", "d"}

    def test_load_raw_itemsets(self):

        raw_itemsets = load_raw_itemsets(
            base_path=DATA_PATH, subdirs=["lst_test", "lst_test_nested"]
        )

        assert "test" in raw_itemsets
        assert len(raw_itemsets["test"]) == 5
        assert "test_nested" in raw_itemsets
        assert len(raw_itemsets["test_nested"]) == 4

    def test_validate_lookup_struct_cache_valid(self):

        cache = {
            "deduce_version": "2.5.0",
            "saved_datetime": "2023-12-06 10:19:39.198133",
            "lookup_structs": "_",
        }

        class MockStats:
            st_mtime = 1000000000  # way in the past

        with patch("pathlib.Path.glob", return_value=[1, 2, 3]):
            with patch("os.stat", return_value=MockStats()):
                assert validate_lookup_struct_cache(
                    cache=cache, base_path=DATA_PATH, deduce_version="2.5.0"
                )

    def test_validate_lookup_struct_cache_file_changes(self):

        cache = {
            "deduce_version": "2.5.0",
            "saved_datetime": "2023-12-06 10:19:39.198133",
            "lookup_structs": "_",
        }

        class MockStats:
            st_mtime = 2000000000  # way in the future

        with patch("pathlib.Path.glob", return_value=[1, 2, 3]):
            with patch("os.stat", return_value=MockStats()):
                assert validate_lookup_struct_cache(
                    cache=cache, base_path=DATA_PATH, deduce_version="2.5.0"
                )

    @patch("deduce.lookup_structs.validate_lookup_struct_cache", return_value=True)
    def test_load_lookup_structs_from_cache(self, _):

        ds_collection = load_lookup_structs_from_cache(
            base_path=DATA_PATH, deduce_version="_"
        )

        assert len(ds_collection) == 2
        assert "test" in ds_collection
        assert "test_nested" in ds_collection

    @patch("deduce.lookup_structs.validate_lookup_struct_cache", return_value=True)
    def test_load_lookup_structs_from_cache_nofile(self, _):

        ds_collection = load_lookup_structs_from_cache(
            base_path=DATA_PATH / "non_existing_dir", deduce_version="_"
        )

        assert ds_collection is None

    @patch("deduce.lookup_structs.validate_lookup_struct_cache", return_value=False)
    def test_load_lookup_structs_from_cache_invalid(self, _):

        ds_collection = load_lookup_structs_from_cache(
            base_path=DATA_PATH, deduce_version="_"
        )

        assert ds_collection is None

    @patch("pickle.dump")
    def test_cache_lookup_structs(self, mock_pickle_dump):

        cache_lookup_structs(
            lookup_structs=dd.ds.DsCollection(),
            base_path=DATA_PATH,
            deduce_version="2.5.0",
        )

        assert mock_pickle_dump.called_once()
