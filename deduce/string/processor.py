import re
from typing import Optional

from docdeid.datastructures import LookupList
from docdeid.str.processor import BaseStringProcessor, LowercaseString


class TakeLastToken(BaseStringProcessor):
    def process_item(self, item: str) -> Optional[str]:
        return item.split(" ")[-1]


class RemoveValues(BaseStringProcessor):
    def __init__(self, filter_values: list[str]):
        self.filter_values = filter_values

    def process_item(self, item: str) -> Optional[str]:

        for filter_value in self.filter_values:

            item = re.sub(
                r"(^"
                + filter_value
                + r"\s|\s"
                + filter_value
                + r"\s|\s"
                + filter_value
                + r"$)",
                "",
                item,
            )

        return item


class Acronimify(BaseStringProcessor):
    def __init__(
        self, min_length: int = 3, split_value: str = " ", join_value: str = ""
    ):
        self.min_length = min_length
        self.split_value = split_value
        self.join_value = join_value

    def process_item(self, item: str) -> Optional[str]:

        item_split = item.split(self.split_value)

        if len(item_split) < self.min_length:
            return None

        return self.join_value.join(x[0] for x in item_split)


class FilterBasedOnLookupList(BaseStringProcessor):
    def __init__(self, filter_list: LookupList, case_sensitive: bool = True):

        self.case_sensitive = case_sensitive

        if case_sensitive:
            self.filter_list = filter_list
        else:
            self.filter_list = LookupList()
            self.filter_list.add_items_from_iterable(
                filter_list, cleaning_pipeline=[LowercaseString()]
            )

    def process_item(self, item: str) -> Optional[str]:

        item_check = item if self.case_sensitive else item.lower()

        if item_check in self.filter_list:
            return None

        return item
