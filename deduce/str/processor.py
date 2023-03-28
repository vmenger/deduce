import re

import docdeid as dd
from docdeid.str import LowercaseString, StringFilter, StringModifier


class TakeLastToken(StringModifier):
    """Take the last token, split by string."""

    def process(self, item: str) -> str:
        return item.split(" ")[-1]


class RemoveValues(StringModifier):
    """
    Remove values as words (between whitespaces, or at start/end of text).

    Arguments:
        filter_values: The values to remove.
    """

    def __init__(self, filter_values: list[str]) -> None:
        self.filter_values = filter_values

    def process(self, item: str) -> str:
        for filter_value in self.filter_values:

            item = re.sub(
                r"(^" + filter_value + r"\s|\s" + filter_value + r"\s|\s" + filter_value + r"$)",
                "",
                item,
            )

        return item


class Acronimify(StringModifier):
    """
    Acronimify, by splitting on string and taking the first character of each 'word'.

    Arguments:
         split_value: The value to split on, default whitespace.
         join_value: The value to join on, default empty string.
    """

    def __init__(self, split_value: str = " ", join_value: str = "") -> None:
        self.split_value = split_value
        self.join_value = join_value

    def process(self, item: str) -> str:
        item_split = item.split(self.split_value)

        return self.join_value.join(x[0] for x in item_split)


class FilterBasedOnLookupSet(StringFilter):
    """
    Filter, based on LookupSet.

    Arguments:
        filter_set: The lookup set, containing the elements to filter
        case_sensitive: Whether to filter case sensitive
    """

    def __init__(self, filter_set: dd.ds.LookupSet, case_sensitive: bool = True) -> None:
        matching_pipeline = None if case_sensitive else [LowercaseString()]

        self.filter_set = dd.ds.LookupSet(matching_pipeline=matching_pipeline)
        self.filter_set.add_items_from_iterable(filter_set)

    def filter(self, item: str) -> bool:
        return item not in self.filter_set
