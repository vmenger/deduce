class NestedTagsError(Exception):
    def __init__(self, msg: str):
        super().__init__(str)
