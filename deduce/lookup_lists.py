""" This module contains all list reading functionality """
import re

from .listtrie import ListTrie
from .utility import read_list
from .tokenizer import tokenize_split

#  Read first names
FIRST_NAMES = read_list("voornaam.lst", min_len=2)

# Read last names
SURNAMES = read_list("achternaam.lst", encoding="utf-8", min_len=2, normalize=True)

# Read interfixes (such as 'van der', etc)
INTERFIXES = read_list("voorvoegsel.lst")

# Read all surnames that frequently occur with an
# interfix ('Jong', 'Vries' for 'de Jong', 'de Vries', etc)
INTERFIX_SURNAMES = list(set([line.strip().split(" ")[-1]
                              for line in read_list("achternaammetvv.lst")]))

# Read prefixes (such as mw, dhr, pt)
PREFIXES = read_list("prefix.lst")

# Read a list of medical terms
MEDTERM = read_list("medischeterm.lst", encoding="latin-1")

# Read the top 1000 of most used words in Dutch, and then filter all surnames from it
TOP1000 = read_list("top1000.lst", encoding="latin-1")
TOP1000 = list(set(TOP1000).difference(read_list("achternaam.lst", lower=True)))

# A list of stop words
STOPWORDS = read_list("stopwoord.lst")

# The whitelist of words that are never annotated as names consists of
# the medical terms, the top1000 words and the stopwords
WHITELIST = list(set([line.lower()
                      for line in MEDTERM + TOP1000 + STOPWORDS if len(line) >= 2]))

### Institutions

# Read the list
INSTITUTIONS = read_list("instellingen.lst", min_len=3)

# These words sometimes occur as the first or final word of the official names of institutions,
# but are not usually referred to as such in the colloquial version
FILTER_VALUES = ["dr.", "der", "van", "de", "het", "'t", "in", "d'"]

# New list of institutions
FILTERED_INSTITUTIONS = []

# Iterate over all institutions
for institution in INSTITUTIONS:

	# Convert to lower case (case matching does not work well for institutions)
    institution = institution.lower()

	# Add stripped version to institutions
    FILTERED_INSTITUTIONS.append(institution.strip())

	# Filter values at start or end of words
    for filter_value in FILTER_VALUES:
        institution = re.sub(
            r"(^" + filter_value + r"\s|\s" + filter_value + r"\s|\s" + filter_value + r"$)",
            "", institution)

	# Again, also add the stripped versions and versions with full stops removed
    FILTERED_INSTITUTIONS.append(institution.strip())
    institution = institution.replace(".", "")
    FILTERED_INSTITUTIONS.append(institution.strip())

	# "st", "st." and "ziekenhuis" have common abbreviations
    if "st" in institution:
        FILTERED_INSTITUTIONS.append(institution.replace("st ", "sint "))

    if "st." in institution:
        FILTERED_INSTITUTIONS.append(institution.replace("st. ", "sint "))

    if "ziekenhuis" in institution:
        FILTERED_INSTITUTIONS.append(institution.replace("ziekenhuis", "zkh"))

	# If the institution name contains 3 or more words, also add the acronym
    if len(institution.split(" ")) >= 3:
        FILTERED_INSTITUTIONS.append("".join(x[0] for x in institution.split(" ")))

# Remove doubles, occurrences on whitelist, and convert back to list
INSTITUTIONS = list(set(FILTERED_INSTITUTIONS).difference(WHITELIST))

### Residences

# Read the list
RESIDENCES = read_list("woonplaats.lst", encoding="utf-8", normalize=True)

# Remove parentheses from the names
RESIDENCES = [re.sub("\(.+\)", "", residence) for residence in RESIDENCES]

# Strip values and remove doubles again
RESIDENCES_SET = set([residence.strip() for residence in RESIDENCES])

# New copy
FILTERED_RESIDENCES = set(RESIDENCES_SET)

# Also add the version with hyphen (-) replaced by whitespace
for residence in RESIDENCES_SET:
    if "-" in residence:
        FILTERED_RESIDENCES.add(re.sub("\-", " ", residence))

# Reinitialize set of RESIDENCES
RESIDENCES_SET = set()

# Remove all RESIDENCES that are on the whitelist
for residence in FILTERED_RESIDENCES:
    if residence.lower() not in WHITELIST:
        RESIDENCES_SET.add(residence)

RESIDENCES = list(RESIDENCES_SET)

### Define some tries, to make lookup faster

INSTITUTION_TRIE = ListTrie()
RESIDENCES_TRIE = ListTrie()

for institution in INSTITUTIONS:
    INSTITUTION_TRIE.add(tokenize_split(institution))

for residence in RESIDENCES:
    RESIDENCES_TRIE.add(tokenize_split(residence))
