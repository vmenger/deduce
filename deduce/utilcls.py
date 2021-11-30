class Token:
    def __init__(self, start_ix: int, end_ix: int, text: str, annotation: str):
        self.start_ix = start_ix
        self.end_ix = end_ix
        self.text = text
        self.annotation = annotation

    def __eq__(self, other):
        return isinstance(other, Token) and self.start_ix == other.start_ix and self.end_ix == other.end_ix and self.text == other.text and self.annotation == other.annotation

    def __repr__(self):
        return self.text + '[' + str(self.start_ix) + ':' + str(self.end_ix) + ']' + (' (ann)' if self.is_annotation() else '')

    def is_annotation(self):
        return self.annotation is not None and self.annotation.strip() != ''

    def get_full_annotation(self):
        return self.annotation

    def subset(self, start_ix: int):
        """

        :param start_ix:
        :return: a new token whose start_ix is the one specified
        """
        return Token(start_ix, self.end_ix, self.text[start_ix:], self.annotation)

class TokenGroup(Token):
    def __init__(self, tokens: list[Token], annotation: str):
        super().__init__(tokens[0].start_ix, tokens[-1].end_ix, ''.join([token.text for token in tokens]), annotation)
        self.tokens = tokens
        self.annotation = annotation

    def __eq__(self, other):
        return isinstance(other, TokenGroup) and self.annotation == other.annotation and len(self.tokens) == len(other.tokens) and all([self.tokens[i] == other.tokens[i] for i in range(len(self.tokens))])

    def __repr__(self):
        return self.text + '[' + str(self.start_ix) + ':' + str(self.end_ix) + ']' + (' (ann)' if self.is_annotation() else '')

    def is_annotation(self):
        return self.annotation.strip() != ''

    def get_full_annotation(self):
        return self.annotation + ''.join([token.get_full_annotation() for token in self.tokens if token.is_annotation()])
