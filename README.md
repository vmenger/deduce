# deduce

[![tests](https://github.com/vmenger/deduce/actions/workflows/test.yml/badge.svg)](https://github.com/vmenger/deduce/actions/workflows/test.yml)
[![coverage](https://coveralls.io/repos/github/vmenger/deduce/badge.svg)](https://coveralls.io/github/vmenger/deduce?branch=master)
[![build](https://github.com/vmenger/deduce/actions/workflows/build.yml/badge.svg)](https://github.com/vmenger/deduce/actions/workflows/build.yml)
[![documentation](https://readthedocs.org/projects/deduce/badge/?version=latest)](https://deduce.readthedocs.io/en/latest/?badge=latest)
![pypi version](https://img.shields.io/pypi/v/deduce)
![pypi python versions](https://img.shields.io/pypi/pyversions/deduce)
![pypi downloads](https://img.shields.io/pypi/dm/deduce)
![license](https://img.shields.io/github/license/vmenger/deduce)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Installation](#installation) - [Versions](#versions) - [Getting Started](#getting-started) - [Documentation](#documentation) - [Contributiong](#contributing) - [Authors](#authors) - [License](#license)

<!-- start include in docs -->

> Deduce 2.0.0 has been released! It includes a 10x speedup, and way more features for customizing and tailoring. Some small changes are needed to keep going from version 1, read more about it here: [docs/migrating-to-v2](https://deduce.readthedocs.io/en/latest/migrating.html)

De-identify clinial text written in Dutch using `deduce`, a rule-based de-identification method for Dutch clinical text.

The development, principles and validation of `deduce` were initially described in [Menger et al. (2017)](http://www.sciencedirect.com/science/article/pii/S0736585316307365). De-identification of clinical text is needed for using text data for analysis, to comply with legal requirements and to protect the privacy of patients. Our rule-based method removes Protected Health Information (PHI) in the following categories:

* Person names, including initials
* Geographical locations smaller than a country
* Names of institutions that are related to patient treatment
* Dates
* Ages
* Patient numbers
* Telephone numbers
* E-mail addresses and URLs

If you use `deduce`, please cite the following paper:  

[Menger, V.J., Scheepers, F., van Wijk, L.M., Spruit, M. (2017). DEDUCE: A pattern matching method for automatic de-identification of Dutch medical text, Telematics and Informatics, 2017, ISSN 0736-5853](http://www.sciencedirect.com/science/article/pii/S0736585316307365)

## Installation

``` python
pip install deduce
```

## Versions

For most cases the latest version is suitable, but some specific milestones are:

* `2.0.0` - Major refactor, with speedups, many new options for customizing, functionally very similar to original 
* `1.0.8` - Small bugfixes compared to original release
* `1.0.1` - Original release with [Menger et al. (2017)](http://www.sciencedirect.com/science/article/pii/S0736585316307365)

Detailed versioning information is accessible in the [changelog](CHANGELOG.md). 

<!-- end include in docs -->
<!-- start getting started -->

## Getting started

The basic way to use `deduce`, is to pass text to the `deidentify` method of a `Deduce` object:

```python
from deduce import Deduce

deduce = Deduce()

text = """Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen 
        (e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig 
        in Utrecht. Hij werd op 10 oktober door arts Peter de Visser ontslagen 
        van de kliniek van het UMCU."""

doc = deduce.deidentify(text)
```

The output is available in the `Document` object:

```python
from pprint import pprint

pprint(doc.annotations)

AnnotationSet({Annotation(text='Jan Jansen', start_char=39, end_char=49, tag='persoon', length=10),
               Annotation(text='Peter de Visser', start_char=185, end_char=200, tag='persoon', length=15),
               Annotation(text='j.jnsen@email.com', start_char=76, end_char=93, tag='url', length=17),
               Annotation(text='10 oktober', start_char=164, end_char=174, tag='datum', length=10),
               Annotation(text='patient J. Jansen', start_char=54, end_char=71, tag='persoon', length=17),
               Annotation(text='64', start_char=114, end_char=116, tag='leeftijd', length=2),
               Annotation(text='UMCU', start_char=234, end_char=238, tag='instelling', length=4),
               Annotation(text='06-12345678', start_char=98, end_char=109, tag='telefoonnummer', length=11),
               Annotation(text='Utrecht', start_char=143, end_char=150, tag='locatie', length=7)})

print(doc.deidentified_text)

"""Dit is stukje tekst met daarin de naam <PERSOON-1>. De <PERSOON-2> 
(e: <URL-1>, t: <TELEFOONNUMMER-1>) is <LEEFTIJD-1> jaar oud en woonachtig 
in <LOCATIE-1>. Hij werd op <DATUM-1> door arts <PERSOON-3> ontslagen 
van de kliniek van het <INSTELLING-1>."""
```

Aditionally, if the names of the patient are known, they may be added as `metadata`, where they will be picked up by `deduce`:

```python
from deduce.person import Person

patient = Person(first_names=["Jan"], initials="JJ", surname="Jansen")
doc = deduce.deidentify(text, metadata={'patient': patient})

print (doc.deidentified_text)

"""Dit is stukje tekst met daarin de naam <PATIENT>. De <PATIENT> 
(e: <URL-1>, t: <TELEFOONNUMMER-1>) is <LEEFTIJD-1> jaar oud en woonachtig 
in <LOCATIE-1>. Hij werd op <DATUM-1> door arts <PERSOON-1> ontslagen 
van de kliniek van het <INSTELLING-1>."""
```

As you can see, adding known names keeps references to `<PATIENT>` in text. It also increases recall, as not all known names are contained in the lookup lists. 

<!-- end getting started -->

## Documentation

A more extensive tutorial on using, configuring and modifying `deduce` is available at: [docs/tutorial](https://deduce.readthedocs.io/en/latest/tutorial.html) 

Basic documentation and API are available at: [docs](https://deduce.readthedocs.io/en/latest/)

## Contributing

For setting up the dev environment and contributing guidelines, see: [docs/contributing](https://deduce.readthedocs.io/en/latest/contributing.html)

## Authors

* **Vincent Menger** - *Initial work* 
* **Jonathan de Bruin** - *Code review*
* **Pablo Mosteiro** - *Bug fixes, structured annotations*

## License

This project is licensed under the GNU LGPLv3 license - see the [LICENSE.md](LICENSE.md) file for details