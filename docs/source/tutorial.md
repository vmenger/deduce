# Tutorial

`deduce` is a rule-based de-identification method for clinical text written in Dutch, which finds and removes information in one or more categories of interest (e.g. person names, names of institutions, locations). In principle, `deduce` can work 'out of the box', however, based on both scientific research and personal experience, `deduce` is unlikely to remove all sensitive information when no effort goes into some customization. This tutorial should help you reach that goal. Along with basic steps to get started and highlights of some features, further in this tutorial, we describe how to tailor `deduce` to your specific data. 

It's useful to note that from version `2.0.0`, `deduce` is built using `docdeid`([docs](https://docdeid.readthedocs.io/en/latest/), [GitHub](https://github.com/vmenger/docdeid)), a small framework that helps build de-identifiers. Before you start customizing `deduce`, checking the `docdeid` docs will probably make it easier still.  

In case you get stuck with applying or modifying `deduce`, its always possible to as for help, by creating an issue in our [issue tracker](https://github.com/vmenger/deduce/issues)!

```{include} ../../README.md
:start-after: <!-- start getting started -->
:end-before: <!-- end getting started -->
```

## Included components

A `docdeid` de-identifier is made up of document processors, such as annotators, annotation processors, and redactors, that are applied sequentially in a pipeline. The most important components that make up `deduce` are described below.  

### Annotators

The `Annotator` is responsible for tagging pieces of information in the text as sensitive information that needs to be removed. `deduce` includes various annotators, described below:

| **Group**       | **Annotator name**       | **Annotator type** | **Matches**                                                                                |
|-----------------|--------------------------|--------------------|--------------------------------------------------------------------------------------------|
| names           | prefix_with_name         | pattern            | A prefix followed by a word starting with an uppercase                                     |
|                 | interfix_with_name       | pattern            | An interfix followed by a word starting with an uppercase                                  |
|                 | initial_with_capital     | pattern            | An initial followed by a word starting with an uppercase                                   |
|                 | initial_interfix         | pattern            | An initial followed by an interfix and a word starting with an uppercase                   |
|                 | first_name_lookup        | pattern            | A first name based on builtin lookup lists                                                 |
|                 | surname_lookup           | pattern            | A surname based on builtin lookup lists                                                    |
|                 | person_first_name        | pattern            | First name of the patient, based on metadata (fuzzy)                                       |
|                 | person_initial_from_name | pattern            | Initial of patient, based on first names in metadata                                       |
|                 | person_initials          | pattern            | Initials of patient, based on metadata                                                     |
|                 | person_surname           | pattern            | Surname of patient, based on metadata (fuzzy)                                              |
|                 | annotation_context       | context pattern    | Multiple based on context, e.g. an annotation of a name followed by another word starting with an uppercase |
| institutions    | institution              | multi token lookup | Institutions, based on builtin lookup lists                                                |
| locations       | residence                | multi token lookup | Residences, based on builtin lookup lists                                                  |
|                 | street_with_number       | regexp             | Street names, with optionally a house number                                               |
|                 | postal_code              | regexp             | Postal codes                                                                               |
|                 | postbus                  | regexp             | Postbussen                                                                                 |
| dates           | date_dmy_1               | regexp             | Dates dmy format (pattern 1)                                                               |
|                 | date_dmy_2               | regexp             | Dates dmy format (pattern 2)                                                               |
|                 | date_ymd_1               | regexp             | Dates ymd format (pattern 1)                                                               |
|                 | date_ymd_2               | regexp             | Dates ymd format (pattern 2)                                                               |
| ages            | age                      | regexp             | Ages                                                                                       |
| identifiers     | identifier               | regexp             | Identifiers (7+ digit numbers)                                                             |
|                 | bsn                      | custom             | BSN-numbers (9 digits + specific 'elfproef')                                               |
| phone_numbers   | phone                    | regexp             | Phone numbers                                                                              |
| email_addresses | email                    | regexp             | E-mail addresses                                                                           |
| urls            | url                      | regexp             | URLs                                                                                       |

It's possible to add, remove, apply subsets or implement custom annotators, those options are described further down under [customizing deduce](#customizing-deduce). 

### Other processors

In addition to annotators, a `docdeid` de-identifier contains annotation processors, which do some operation to the set of annotations generated previously, and redactors, which take the annotation and replace them in the text. Other processors included in `deduce` are listed below:

| **Name**                   | **Group**       | **Description**                                                                                       |
|----------------------------|-----------------|-------------------------------------------------------------------------------------------------------|
| overlap_resolver           | post_processing | Makes sure overlap among annotations is resolved.                                                     |
| merge_adjacent_annotations | post_processing | If there are any adjacent annotations with the same tag, they are merged into a single annotation.    |
| redactor                   | post_processing | Takes care of replacing the annotated PHIs with `<TAG>` (e.g. `<LOCATION-1>`, `<DATE-2>`)             |

### Lookup sets

In order to match tokens to known identifiable words or concepts, `deduce` has the following builtin lookup sets:

| **Name**          | **Size** | **Examples**                                     |
|-------------------|----------|--------------------------------------------------|
| first_names       | 9010     | Laurentia, Janny, Chantall                       |
| surnames          | 7767     | Bosland, Winkler, Lunenburg                      |
| interfixes        | 274      | Bij 't, Onder 't, Bij de                         |
| interfix_surnames | 1920     | Geldorp, Haaster, Overbeek                       |
| prefixes          | 23       | ggn, mr, pt                                      |
| whitelist         | 1176     | delen, temesta, lepel                            |
| institutions      | 827      | slingeland ziekenhuis, slingeland zkh, maliebaan |
| residences        | 2504     | Oude Wetering, Noordeinde, Jelsum                |

## Customizing deduce

We highly recommend making some effort to customize `deduce`, as even some basic effort will almost surely increase accuracy. Below are outlined some ways to achieve this, including: making changes to `config.json`, adding/removing custom pipeline components, and modifying the builtin lookup sets.

### Changing `config.json`

A default `config.json` ([source on GitHub](https://github.com/vmenger/deduce/blob/main/config.json)) file is packaged with `deduce`. Among with some basic settings, it defines all annotators (also listed above). It's possible to add, modify or delete annotators here (e.g. changing regular expressions). After modifying `config.json`, you should save the modified `.json` and pass the path as argument when initializing `Deduce`:

```python
from deduce import Deduce

deduce = Deduce(config_file="path/to/custom_config.json")
```

Note that some more basic configuration options can be adjusted in the config file, however, more config options will be added in the future. 


### Using `disabled` keyword to disable components

It's possible to disable specific (groups of) annotators or processors when deidentifying a text. For example, to apply all annotators, except those in the dates group: 

```python
from deduce import Deduce

deduce = Deduce()
deduce.deidentify(text, disabled={'dates'})
```

Or, to disable one specific URL annotator in the URLs group, but keeping the other URL patterns:

```python
from deduce import Deduce

deduce = Deduce()
deduce.deidentify("text", disabled={'urls_1'})
```

### Using `enabled` keyword

Although it's also possible to _enable_ only some processors, this is only useful in a limited amount of cases. You must manually specify the groups, individual annotators, and postprocessors to have a sensible output. For example, to de-identify only e-mail addresses, use:

```python
from deduce import Deduce

deduce = Deduce()
deduce.deidentify("text", enabled={
    'urls', # annotator group, with annotators:
    'email', 
    'post_processing', # post processing group, with processors:
    'overlap_resolver',
    'merge_adjacent_annotations',
    'redactor'
})
```

The following example however will apply **no annotators**, as the `email` annotator is enabled, but its' group `urls` is not: 

```python
from deduce import Deduce

deduce = Deduce()
deduce.deidentify("text", enabled={'email'})
```

### Implementing custom components

It's possible to implement the following custom components,  `Annotator`, `AnnotationProcessor`, `Redactor` and `Tokenizer`. This is done by implementing the abstract classes defined in the `docdeid` package, which is described here: [docdeid docs - docdeid components](https://docdeid.readthedocs.io/en/latest/tutorial.html#docdeid-components).

In our case, we can add or remove custom document processors by interacting with the `deduce.processors` attribute directly:

```python
from deduce import Deduce

deduce = Deduce()

# remove date annotators
del deduce.processors['dates']

# add another annotator
deduce.processors.add_processor( 
    'some_new_category', 
    MyCustomAnnotator(), 
    position=0
) 
```

Note that by default, processors are applied in the order they are added to the pipeline. To prevent a new annotator being added after the `post_processing` group (meaning the annotations would not be redacted in the text), use the `position` keyword of the `add_processor` method, as in the example above.

#### Changing tokenizer

There might be a case where you want to add a custom annotator to `deduce` that requires its own tokenizing logic. Although replacing the builtin tokenizer is not recommended, as builtin annotators depend on it, it's possible to add more tokenizers as follows:

```python
from deduce import Deduce

deduce = Deduce()
deduce.tokenizers['my_custom_tokenizer'] = MyCustomTokenizer() # make sure this implements abstract docdeid.tokenize.Tokenizer
```

Then annotators can use:

```python
import docdeid as dd

def annotate(doc: dd.Document):
    tokens = doc.get_tokens("my_custom_tokenizer")
```

### Tailoring lookup sets

Updating the builtin lookup sets is a very useful and straightforward way to tailor `deduce`. Changes can be made directly from the `Deduce.lookup_sets` attribute, as such: 

```python
from deduce import Deduce

deduce = Deduce()

deduce.lookup_sets['first_names'].add_items_from_iterable(["naam", "andere_naam"])
deduce.lookup_sets['whitelist'].add_items_from_iterable(["woord", "ander_woord"])
deduce.lookup_sets['residences'].add_items_from_iterable(["kleine plaats in de regio"])
deduce.lookup_sets['institutions'].add_items_from_iterable(["verzorgingstehuis hier om de hoek"])

# need to re-initialize the doc processors, so they know about updated lookup_sets
deduce.initialize_doc_processors()

```

After making changes to `lookup_sets`, it's important to call `Deduce.initialize_doc_processors`, so that the changes get picked up by the annotators. Full documentation on lookup sets and how to modify them is available in the [docdeid API](https://docdeid.readthedocs.io/en/latest/api/docdeid.ds.html#docdeid.ds.lookup.LookupSet).
