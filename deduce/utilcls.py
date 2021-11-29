class Token:
    def __init__(self, text: str, start_ix: int, end_ix: int):
        """
        IMPORTANT: all class members must be immutable so that the hash is immutable too
        :param text: the text contained in the token
        :param start_ix: the start index in the text where the token was extracted from
        :param end_ix:  the end index in the text where the token was extracted from
        """
        self.text = text
        self.start_ix = start_ix
        self.end_ix = end_ix
        assert self.end_ix >= self.start_ix
        assert self.end_ix - self.start_ix == len(self.text)

    def __repr__(self):
        return self.text + "[" + str(self.start_ix) + ":" + str(self.end_ix) + "]"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return self.text == other.text and self.start_ix == other.start_ix and self.end_ix == other.end_ix

    def __hash__(self):
        return hash((self.text, self.start_ix, self.end_ix))


class Annotation:
    def __init__(self, start_ix: int, end_ix: int, tag: str, text: str):
        """

        :param start_ix: index in original text where annotation starts
        :param end_ix: index in original text where annotation ends
        :param tag: category of annotation
        :param text: text contained in the annotation -> SHOULD NOT BE PRINTED
        """
        self.start_ix = start_ix
        self.end_ix = end_ix
        self.tag = tag
        self.text_ = text

    def __eq__(self, other):
        if not isinstance(other, Annotation):
            return False
        return self.start_ix == other.start_ix and self.end_ix == other.end_ix and \
               self.tag == other.tag and self.text_ == other.text_

    def __repr__(self):
        return self.tag + "[" + str(self.start_ix) + ":" + str(self.end_ix) + "]"

    def to_text(self):
        return "<" + self.tag + " " + self.text_ + ">"

    @staticmethod
    def join_and_sort(old_annotations: list, new_annotations: list) -> list:
        return sorted(old_annotations + new_annotations, key=lambda x: x.start_ix)


class InvalidTokenError(ValueError):
    def __init__(self, code: str):
        super().__init__()
        self.code = code

def replace_tag(annotation: Annotation, new_tag: str) -> Annotation:
    return Annotation(annotation.start_ix, annotation.end_ix, new_tag, annotation.text_)
