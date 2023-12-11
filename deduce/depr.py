import warnings

import docdeid as dd

warnings.simplefilter(action="default")


class DeprecatedDsCollection(dd.ds.DsCollection):
    """Temporary deprecation wrapper."""

    def __init__(self, deprecated_items: dict, *args, **kwargs) -> None:
        self.deprecated_items = deprecated_items
        self.deprecated_lists = {
            k: dd.ds.LookupSet() for k, v in deprecated_items.items() if v is None
        }
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: str) -> dd.ds.Datastructure:
        if key in self.deprecated_items:

            new_key = self.deprecated_items[key]

            if new_key is None:

                warnings.warn(
                    f"The lookup structure with key {key} is no longer "
                    f"included in Deduce. If it was a list with exceptions, "
                    f"it is now automatically included in the normal list.",
                    DeprecationWarning,
                )

                return self.deprecated_lists[key]

            warnings.warn(
                f"The lookup structure with key {key} has been replaced "
                f"with {new_key}, pleace replace it accordingly in your "
                f"code/config",
                DeprecationWarning,
            )

            return super().__getitem__(new_key)

        return super().__getitem__(key)
