import docdeid as dd


def link_tokens(tokens: list[dd.Token]):

    for token, next_token in zip(tokens, tokens[1:]):
        token.set_next_token(next_token)
        next_token.set_previous_token(token)

    return tokens


def linked_tokens(tokens: list[str]) -> list[dd.Token]:

    tokens = [dd.Token(x, 0, len(x)) for x in tokens]

    return link_tokens(tokens)
