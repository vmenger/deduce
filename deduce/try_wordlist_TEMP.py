from pathlib import Path

import dutch_words


def common_word_list():
    words = dutch_words.get_ranked()

    print("knop" in words)

    capital_split = {True: [], False: []}
    for w in reversed(words):
        capital_split[w[0].isupper()].append(w)

    print("Capitalized words:", len(capital_split[True]))
    print("Not capitalized words:", len(capital_split[False]))

    # for s, e in [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50)]:
    #     print("Capitalized:", s, "to", e, "words:")
    #     for w in capital_split[True][s:e]:
    #         print(w)
    #     print("Not capitalized:", s, "to", e, "words:")
    #     for w in capital_split[False][s:e]:
    #         print(w)
    #     input("Press enter to continue")

    used_common_word_list = []
    path = Path("data/lookup/src/whitelist/lst_common_word/items.txt")
    with open(path, "r") as f:
        for line in f:
            used_common_word_list.append(line.strip())

    diff_set = set(capital_split[False]) - set(used_common_word_list)
    print("\n\n=========diff common words:\n")
    for w in diff_set:
        print(w)

    print(
        f"\n\n=========diff common words count: {len(diff_set)} out of {len(capital_split[False])}\n"
    )

    output_path = Path("/data/lookup/src/whitelist/lst_common_word/extra_items.txt")
    with open(output_path, "w") as f:
        for w in diff_set:
            f.write(w + "\n")


def names_list():
    pass


if __name__ == "__main__":
    common_word_list()
    # names_list()
    pass
