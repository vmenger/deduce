# Deduce: de-identification method for Dutch medical text
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> If you are looking for the version of DEDUCE as published with [Menger et al (2017)](http://www.sciencedirect.com/science/article/pii/S0736585316307365), please visit [vmenger/deduce-classic](https://github.com/vmenger/deduce-classic/), where the original is archived. This version is maintained and improved, thus possibly differing from the validated original.

This project contains the code for DEDUCE: de-identification method for Dutch medical text, initially described in [Menger et al (2017)](http://www.sciencedirect.com/science/article/pii/S0736585316307365). De-identification of medical text is needed for using text data for analysis, to comply with legal requirements and to protect the privacy of patients. Our pattern matching based method removes Protected Health Information (PHI) in the following categories:

1. Person names, including initials
2. Geographical locations smaller than a country
3. Names of institutions that are related to patient treatment
4. Dates
5. Ages
6. Patient numbers
7. Telephone numbers
8. E-mail addresses and URLs

The details of the development and workings of the initial method, and its validation can be found in: 

[Menger, V.J., Scheepers, F., van Wijk, L.M., Spruit, M. (2017). DEDUCE: A pattern matching method for automatic de-identification of Dutch medical text, Telematics and Informatics, 2017, ISSN 0736-5853](http://www.sciencedirect.com/science/article/pii/S0736585316307365)

### Prerequisites

* `nltk`

### Installing

Installing can be done through pip and git: 

``` python
>>> pip install deduce
```

Or from source, simply download and use python to install:

``` python
>>> python setup.py install
```

## Getting started

The package has a method for annotating (`annotate_text`) and for removing the annotations (`deidentify_annotations`).

``` python

import deduce 

deduce.annotate_text(
        text,                       # The text to be annotated
        patient_first_names="",     # First names (separated by whitespace)
        patient_initials="",        # Initial
        patient_surname="",         # Surname(s)
        patient_given_name="",      # Given name
        names=True,                 # Person names, including initials
        locations=True,             # Geographical locations
        institutions=True,          # Institutions
        dates=True,                 # Dates
        ages=True,                  # Ages
        patient_numbers=True,       # Patient numbers
        phone_numbers=True,         # Phone numbers
        urls=True,                  # Urls and e-mail addresses
        flatten=True                # Debug option
    )    
    
deduce.deidentify_annotations(
        text                        # The annotated text that should be de-identified
    )
    
```

## Examples
``` python
>>> import deduce

>>> text = u"Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen (e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud 
    en woonachtig in Utrecht. Hij werd op 10 oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
>>> annotated = deduce.annotate_text(text, patient_first_names="Jan", patient_surname="Jansen")
>>> deidentified = deduce.deidentify_annotations(annotated)

>>> print (annotated)
"Dit is stukje tekst met daarin de naam <PATIENT Jan Jansen>. De <PATIENT patient J. Jansen> (e: <URL j.jnsen@email.com>, t: <TELEFOONNUMMER 06-12345678>) 
is <LEEFTIJD 64> jaar oud en woonachtig in <LOCATIE Utrecht>. Hij werd op <DATUM 10 oktober> door arts <PERSOON Peter de Visser> ontslagen van de kliniek van het <INSTELLING umcu>."
>>> print (deidentified)
"Dit is stukje tekst met daarin de naam <PATIENT>. De <PATIENT> (e: <URL-1>, t: <TELEFOONNUMMER-1>) is <LEEFTIJD-1> jaar oud en woonachtig in <LOCATIE-1>.
Hij werd op <DATUM-1> door arts <PERSOON-1> ontslagen van de kliniek van het <INSTELLING-1>."
```

### Configuring

The lookup lists in the `data/` folder can be tailored to the users specific needs. This is especially recommended for the list of names of institutions, since they are by default tailored to location of development and testing of the method. Regular expressions can be modified in `annotate.py`, this is for the same reason recommended for detecting patient numbers. 

## Contributing

Thanks a lot for considering to make a contribution to DEDUCE, we are very open to your help!

* If you need support, have a question, or found a bug/error, please get in touch by [creating a New Issue](https://github.com/vmenger/deduce/issues). We don't have an issue template, just try to be specific and complete, so we can tackle it. 
* If you want to make a contribution either to the code or the docs, please take a few minutes to read our [contribution guidelines](CONTRIBUTING.md). This greatly improve the chances of your work being merged into the repository.

## Changelog

You may find detailed versioning information in the [changelog](CHANGELOG.md).

## Authors

* **Vincent Menger** - *Initial work* 
* **Jonathan de Bruin** - *Code review*
* **Pablo Mosteiro** - *Bug fixes, structured annotations*

## License

This project is licensed under the GNU LGPLv3 license - see the [LICENSE.md](LICENSE.md) file for details
