import re
from typing import Optional

import docdeid as dd
from docdeid.str.processor import BaseStringFilter, BaseStringModifier, LowercaseString


class TakeLastToken(BaseStringModifier):
    def process(self, item: str) -> Optional[str]:
        return item.split(" ")[-1]


class RemoveValues(BaseStringModifier):
    def __init__(self, filter_values: list[str]) -> None:
        self.filter_values = filter_values

    def process(self, item: str) -> Optional[str]:

        for filter_value in self.filter_values:

            item = re.sub(
                r"(^" + filter_value + r"\s|\s" + filter_value + r"\s|\s" + filter_value + r"$)",
                "",
                item,
            )

        return item


class Acronimify(BaseStringModifier):
    def __init__(self, split_value: str = " ", join_value: str = "") -> None:
        self.split_value = split_value
        self.join_value = join_value

    def process(self, item: str) -> Optional[str]:

        item_split = item.split(self.split_value)

        return self.join_value.join(x[0] for x in item_split)


class FilterBasedOnLookupSet(BaseStringFilter):
    def __init__(self, filter_set: dd.LookupSet, case_sensitive: bool = True) -> None:

        matching_pipeline = None if case_sensitive else [LowercaseString()]

        self.filter_set = dd.LookupSet(matching_pipeline=matching_pipeline)
        self.filter_set.add_items_from_iterable(filter_set)

    def filter(self, item: str) -> bool:

        return item not in self.filter_set
