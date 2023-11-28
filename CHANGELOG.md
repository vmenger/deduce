# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2.5.0 (2023-11-28)

### Added
- the `RegexpPseudoAnnotator` component for filtering regexp matches based on preceding/following words
- a `prefix_with_interfix` pattern for names, detecting e.g. `Dr. van Loon`

### Fixed
- a bug with `BsnAnnotator` with non-digit characters in regexp

### Changed
- the age detection component, with improved logic and pseudo patterns
- annotations are no longer counted adjacent when separated by a comma
- streets are prioritized over names when merging overlapping annotations
- removed some false positives for postal codes ending in `gr` or `ie`
- extended the postbus pattern for `xx.xxx` format (old notation)
- some smaller optimizations and exceptions for institution, hospital, placename, residence, medical term, first name, and last name lookup lists

## 2.4.2 (2023-11-22)

### Changed
- multi-token lookup for first- and last names, so multi token names are now detected
- some small lookup list additions

## 2.4.3 (2023-11-22)

### Changed
- extended list of medical terms

## 2.4.2 (2023-11-21)

### Changed
- name lookup list contents, extending names and adding more exceptions

## 2.4.1 (2023-11-15)

### Added
- detection of initials `Ch.`, `Chr.`, `Ph.` and `Th.` 

## 2.4.0 (2023-11-15)

### Added
- logic for detecting hospitals, with added whitelist and separate annotator

### Changed
- logic for detecting (non-hospital) institutions, with extended lookup list

### Removed
- the separate Altrecht annotator, now included in the lookup list

## 2.3.1 (2023-11-01)

### Fixed
- include data files recursively in package

## 2.3.0 (2023-10-25)

### Added
- lookup lists (and logic) for Dutch provinces, regions, municipalities and streets

### Changed
- name of `residences` annotator to `placenames`, now includes provinces, regions and municipalities
- lookup lists (and logic) for residences
- logic for streets, housenumber and housenumber letters

## 2.2.0 (2023-09-28)

### Changed
- tokenizer logic: 
  - a token is now a sequence of alphanumeric characters, a single newline, or a single special character. 
  - whitespaces are no longer considered tokens
- moved token pattern logic to config, using a new `TokenPatternAnnotator`
- moved context pattern logic to config, using a new `ContextAnnotator`
- many updates to name detection logic
  - lookup list optimizations
  - added, removed and simplified patterns

## 2.1.0 (2023-08-07)

### Added
- a component for deidentifying BSN-nummers

### Changed
- updated dependencies
- by default, deduce now recognizes and tags bsn nummers
- by default, deduce now recognizes all other 7+ digit numbers as identifiers
- improved regular expressions for e-mail address and url matching, with separate tags
- logic for detecting phone numbers (improvements for hyphens, whitespaces, false positive identifiers)
- improved regular expression for age matching
- date detection logic:
  - now only recognizes combinations of day, month and year (day/month combinations caused many false positives)
  - detects year-month-day format in addition to (day-month-year)
- loading a custom config now only replaces the config options that are explicitly set, using defaults for those not included in the custom config

### Fixed
- annotations can no longer be counted as adjacent when separated by newline or tab (and will thus not be merged)

### Removed
- a separate patient identifier tag, now superseded by a generic tag
- detection of day/month combinations for dates, as this caused many false positives (e.g. lab values, numeric scores) 

### Deprecated
- backwards compatibility, which was temporary added to transition from v1 to v2

## 2.0.3 (2023-04-06)

### Fixed
- removed 'decibutus' from list of institutions as it caused many false positives

## 2.0.2 (2023-03-28)

### Changed
- upgraded dependencies, including `markdown-it-py` which had a vulnerability

## 2.0.1 (2022-12-09)

### Changed
- upgraded dependencies

## 2.0.0 (2022-12-05)

### Changed
- major refactor that touches pretty much every line of code
- use `docdeid` package for logic
- speedups: now 973% faster
- use lookup sets instead of lookup lists
- refactor tokenizer
- refactor annotators into separate classes, using structured annotations
- guidelines for contributing

### Added
- introduced new interface for deidentification, using `Deduce()` class
- a separate documentation page, with tutorial and migration guide
- support for python 3.10 and 3.11


### Removed
- the `annotate_text` and `deidentify_annotations` functions
- all in-text annotation (under the hood) and associated functions
- support for given names. given names can be added as another first name in the `Person` class. 
- support for python 3.7 and 3.8

### Fixed
- `<` and `>` are no longer replaced by `(` and `)` respectively
- deduce does not strip text (whitespaces, tabs at beginning/end of text) anymore

## 1.0.8 (2021-11-29)

### Fixed
- various modifications related to adding or subtracting spaces in annotated texts
- remove the lowercasing of institutions' names
- therefore, all structured annotations have texts matching the original text in the same span

### Added
- warn if there are any structured annotations whose annotated text does not match the original text in the span denoted by the structured annotation

## 1.0.7 (2021-11-03)

### Changed
- Internal code formatting improvements

### Added
- Contributing guidelines

## 1.0.6 (2021-10-06)

### Fixed
- Bug with multiple 4-digit mg dosages in one text

## 1.0.5 (2021-10-05)

### Fixed
- Minor bug where tag flattening had no effect

## 1.0.4 (2021-10-05)

### Added
- Changelog
- Additional unit tests for whitespace/punctuation

### Fixed
- Various whitespace/punctuation bugs
- Bug with nested tags not related to person names
- Bug with adjacent tags not being merged

## 1.0.3 (2021-07-07)

### Added
- Structured annotations
- Some unit tests

### Fixed
- Error with outdated unicode package
- Bug with context

## 1.0.2 
Release to PyPI

## 1.0.1 
Small bugfix for None as input

## 1.0.0 
Initial version
