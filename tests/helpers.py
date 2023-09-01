import docdeid as dd

from deduce.tokenizer import DeduceToken

def link_tokens(tokens: list[DeduceToken]):
    for token, next_token in zip(tokens, tokens[1:]):
        token.set_next_token(next_token)
        next_token.set_previous_token(token)

    return tokens


def linked_tokens(tokens: list[str]) -> list[DeduceToken]:
    tokens = [DeduceToken(x, 0, len(x)) for x in tokens]

    return link_tokens(tokens)
