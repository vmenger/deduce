class AbstractSpan:
    # TODO: turn this into an interface by removing the member variables and creating getters instead
    def __init__(self, start_ix: int, end_ix: int, text: str, annotation=None):
        self.start_ix = start_ix
        self.end_ix = end_ix
        self.text = text
        self.annotation = annotation

    def __repr__(self):
        return self.text + \
               '[' + str(self.start_ix) + ':' + str(self.end_ix) + ']' + \
               (' (' + self.annotation + ')' if self.is_annotation() else '')

    def flatten(self, with_annotation=None):
        """
        Flatten nested annotations
        :param with_annotation: if not None, use the new annotation; if None, use the concatenation of all annotations
        :return: a new instance with the new annotation
        """
        raise NotImplementedError('Abstract class')

    def get_full_annotation(self) -> str:
        raise NotImplementedError('Abstract class')

    def is_annotation(self) -> bool:
        raise NotImplementedError('Abstract class')

    def with_annotation(self, new_annotation: str):
        # Return a new instance with a different annotation
        raise NotImplementedError('Abstract class')

    def as_text(self) -> str:
        """
        :return: the text plus annotation. If it's a TokenGroup, include nested tags
        """
        raise NotImplementedError('Abstract class')

class Token(AbstractSpan):
    def __init__(self, start_ix: int, end_ix: int, text: str, annotation: str):
        super().__init__(start_ix, end_ix, text, annotation)

    def __eq__(self, other):
        return isinstance(other, Token) \
               and self.start_ix == other.start_ix \
               and self.end_ix == other.end_ix \
               and self.text == other.text \
               and self.annotation == other.annotation

    def flatten(self, with_annotation=None):
        return Token(self.start_ix, self.end_ix, self.text, with_annotation) \
            if with_annotation and with_annotation.strip() \
            else self

    def remove_annotation(self):
        return Token(self.start_ix, self.end_ix, self.text, '')

    def is_annotation(self):
        return self.annotation is not None and self.annotation.strip() != ''

    def with_annotation(self, new_annotation: str):
        return Token(self.start_ix, self.end_ix, self.text, new_annotation)

    def get_full_annotation(self):
        return self.annotation

    def subset(self, start_ix: int):
        """

        :param start_ix:
        :return: a new token whose start_ix is the one specified
        """
        return Token(start_ix, self.end_ix, self.text[start_ix:], self.annotation)

    def as_text(self) -> str:
        return '<' + self.annotation + ' ' + self.text + '>' if self.is_annotation() else self.text

class TokenGroup(AbstractSpan):
    def __init__(self, tokens: list[AbstractSpan], annotation: str):
        super().__init__(tokens[0].start_ix, tokens[-1].end_ix, ''.join([token.text for token in tokens]), annotation)
        self.tokens = tokens

    def __eq__(self, other):
        return isinstance(other, TokenGroup) \
               and self.annotation == other.annotation \
               and len(self.tokens) == len(other.tokens) \
               and all([self.tokens[i] == other.tokens[i] for i in range(len(self.tokens))])

    def flatten(self, with_annotation=None):
        annotation = with_annotation if with_annotation and with_annotation.strip() else self.get_full_annotation()
        daughter_spans = self.get_flat_token_list(remove_annotations=True)
        return TokenGroup(daughter_spans, annotation)

    def is_annotation(self):
        return self.annotation.strip() != ''

    def with_annotation(self, new_annotation: str):
        return TokenGroup(self.tokens, new_annotation)

    def get_full_annotation(self):
        return self.annotation + \
               ''.join([token.get_full_annotation() for token in self.tokens if token.is_annotation()])

    def get_flat_token_list(self, remove_annotations: bool) -> list:
        """
        Given a list of nested spans, return a flat token list
        :param remove_annotations: whether annotations should be removed from the individual tokens
        :return: a flat list of tokens
        """
        tokens = []
        for span in self.tokens:
            if isinstance(span, TokenGroup):
                tokens += span.get_flat_token_list(remove_annotations)
            elif isinstance(span, Token):
                tokens.append(span.remove_annotation() if remove_annotations else span)
            else:
                raise NotImplementedError('Unknown type', type(span))
        return tokens

    def as_text(self) -> str:
        text = ''.join([s.as_text() for s in self.tokens])
        return '<' + self.annotation + ' ' + text + '>' if self.is_annotation() else text
