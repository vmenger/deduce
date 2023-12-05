import unittest
from pathlib import Path

from deduce.lookup_structs import apply_transform, load_raw_itemset, load_raw_itemsets

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
