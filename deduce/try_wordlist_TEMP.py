import dutch_words

words = dutch_words.get_ranked()

print("knop" in words)

capital_split = {True: [], False: []}
for w in reversed(words):
    capital_split[w[0].isupper()].append(w)

print("Capitalized words:", len(capital_split[True]))
print("Not capitalized words:", len(capital_split[False]))

for s, e in [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50)]:
    print("Capitalized:", s, "to", e, "words:")
    for w in capital_split[True][s:e]:
        print(w)
    print("Not capitalized:", s, "to", e, "words:")
    for w in capital_split[False][s:e]:
        print(w)
    input("Press enter to continue")
