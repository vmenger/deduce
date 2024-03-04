import io

from unittest.mock import patch

import docdeid as dd

from deduce.lookup_structs import (
    cache_lookup_structs,
    load_lookup_structs_from_cache,
    load_raw_itemset,
    load_raw_itemsets,
    validate_lookup_struct_cache,
)


class TestLookupStruct:
    def test_load_raw_itemset(self, shared_datadir):

        raw_itemset = load_raw_itemset(
            shared_datadir / "lookup" / "src" / "lst_test")

        assert len(raw_itemset) == 5
        assert "de Vries" in raw_itemset
        assert "De Vries" in raw_itemset
        assert "Sijbrand" in raw_itemset
        assert "Sybrand" in raw_itemset
        assert "Pieters" in raw_itemset
        assert "Wolter" not in raw_itemset

    def test_load_raw_itemset_nested(self, shared_datadir):

        raw_itemset = load_raw_itemset(
            shared_datadir / "lookup" / "src" / "lst_test_nested")

        assert raw_itemset == {"a", "b", "c", "d"}

    def test_load_raw_itemsets(self, shared_datadir):

        raw_itemsets = load_raw_itemsets(
            base_path=shared_datadir / "lookup",
            subdirs=["lst_test", "lst_test_nested"]
        )

        assert "test" in raw_itemsets
        assert len(raw_itemsets["test"]) == 5
        assert "test_nested" in raw_itemsets
        assert len(raw_itemsets["test_nested"]) == 4

    def test_validate_lookup_struct_cache_valid(self, shared_datadir):

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
                    cache=cache,
                    base_path=shared_datadir / "lookup",
                    deduce_version="2.5.0"
                )

    def test_validate_lookup_struct_cache_file_changes(self, shared_datadir):

        cache = {
            "deduce_version": "2.5.0",
            "saved_datetime": "2023-12-06 10:19:39.198133",
            "lookup_structs": "_",
        }

        class MockStats:
            st_mtime = 2000000000  # way in the future

        with patch("pathlib.Path.glob", return_value=[1, 2, 3]):
            with patch("os.stat", return_value=MockStats()):
                assert not validate_lookup_struct_cache(
                    cache=cache,
                    base_path=shared_datadir / "lookup",
                    deduce_version="2.5.0"
                )

    @patch("deduce.lookup_structs.validate_lookup_struct_cache",
           return_value=True)
    def test_load_lookup_structs_from_cache(self, _, shared_datadir):

        ds_collection = load_lookup_structs_from_cache(
            base_path=shared_datadir / "lookup",
            deduce_version="_"
        )

        assert len(ds_collection) == 2
        assert "test" in ds_collection
        assert "test_nested" in ds_collection

    @patch("deduce.lookup_structs.validate_lookup_struct_cache",
           return_value=True)
    def test_load_lookup_structs_from_cache_nofile(self, _, shared_datadir):

        ds_collection = load_lookup_structs_from_cache(
            base_path=shared_datadir / "non_existing_dir",
            deduce_version="_"
        )

        assert ds_collection is None

    @patch("deduce.lookup_structs.validate_lookup_struct_cache",
           return_value=False)
    def test_load_lookup_structs_from_cache_invalid(self, _, shared_datadir):

        ds_collection = load_lookup_structs_from_cache(
            base_path=shared_datadir / "lookup",
            deduce_version="_"
        )

        assert ds_collection is None

    @patch("builtins.open", return_value=io.BytesIO())
    @patch("pickle.dump")
    def test_cache_lookup_structs(self, _, mock_pickle_dump, shared_datadir):

        cache_lookup_structs(
            lookup_structs=dd.ds.DsCollection(),
            base_path=shared_datadir / "lookup",
            deduce_version="2.5.0",
        )

        assert mock_pickle_dump.called_once()
