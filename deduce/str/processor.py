import re
from typing import Optional

from docdeid.ds import LookupList
from docdeid.str.processor import BaseStringFilter, BaseStringModifier, LowercaseString


class TakeLastToken(BaseStringModifier):
    def process(self, item: str) -> Optional[str]:
        return item.split(" ")[-1]


class RemoveValues(BaseStringModifier):
    def __init__(self, filter_values: list[str]):
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
    def __init__(self, split_value: str = " ", join_value: str = ""):
        self.split_value = split_value
        self.join_value = join_value

    def process(self, item: str) -> Optional[str]:

        item_split = item.split(self.split_value)

        return self.join_value.join(x[0] for x in item_split)


class FilterBasedOnLookupList(BaseStringFilter):
    def __init__(self, filter_list: LookupList, case_sensitive: bool = True):

        self.case_sensitive = case_sensitive

        if case_sensitive:
            self.filter_list = filter_list
        else:
            self.filter_list = LookupList()
            self.filter_list.add_items_from_iterable(filter_list, cleaning_pipeline=[LowercaseString()])

    def filter(self, item: str) -> bool:

        item_check = item if self.case_sensitive else item.lower()

        return item_check in self.filter_list
