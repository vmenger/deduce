# Tutorial

`deduce` is a rule-based de-identification method for clinical text written in Dutch, which finds and removes information in one or more categories of interest (e.g. person names, names of institutions, locations). In principle, `deduce` can work 'out of the box', however, based on both scientific research and personal experience, `deduce` is unlikely to remove all sensitive information when no effort goes into some customization. This tutorial should help you reach that goal. Along with basic steps to get started and highlights of some features, further in this tutorial, we describe how to tailor `deduce` to your specific data. 

It's useful to note that from version `2.0.0`, `deduce` is built using `docdeid`([docs](https://docdeid.readthedocs.io/en/latest/), [GitHub](https://github.com/vmenger/docdeid)), a small framework that helps build de-identifiers. Before you start customizing `deduce`, checking the `docdeid` docs will probably make it easier still.  

In case you get stuck with applying or modifying `deduce`, its always possible to ask for help, by creating an issue in our [issue tracker](https://github.com/vmenger/deduce/issues)!

```{include} ../../README.md
:start-after: <!-- start getting started -->
:end-before: <!-- end getting started -->
```

## Included components

A `docdeid` de-identifier is made up of document processors, such as annotators, annotation processors, and redactors, that are applied sequentially in a pipeline. The most important components that make up `deduce` are described below.

### Annotators

The `Annotator` is responsible for tagging pieces of information in the text as sensitive information that needs to be removed. `deduce` includes various annotators, described below:

| Group           | Annotator Name       | Annotator Type                              | Explanation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|-----------------|----------------------|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| names           | prefix_with_initial  | `deduce.annotator.TokenPatternAnnotator`    | Matches a prefix followed by initial(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|                 | prefix_with_interfix | `deduce.annotator.TokenPatternAnnotator`    | Matches a prefix followed by an interfix and something that resembles a name                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|                 | prefix_with_name     | `deduce.annotator.TokenPatternAnnotator`    | Matches a prefix followed by something that resembles a name                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|                 | interfix_with_name   | `deduce.annotator.TokenPatternAnnotator`    | Matches an interfix followed by something that resembles a name                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|                 | initial_with_name    | `deduce.annotator.TokenPatternAnnotator`    | Matches an initial followed by something that resembles a name                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|                 | initial_interfix     | `deduce.annotator.TokenPatternAnnotator`    | Matches an initial followed by an interfix and something that resembles a name                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|                 | first_name_lookup    | `docdeid.process.MultiTokenLookupAnnotator` | Lookup based on first names from Voornamenbank (Meertens Instituut)                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|                 | surname_lookup       | `docdeid.process.MultiTokenLookupAnnotator` | Lookup based on surnames from Familienamenbank (Meertens Instituut)                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|                 | patient_name         | `deduce.annotator.PatientNameAnnotator`     | Custom logic to match patient name, if supplied in document metadata                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|                 | name_context         | `deduce.annotator.ContextAnnotator`         | Matches names based on annotations found above, with the following context patterns:  `interfix_right`: An interfix and something that resembles a name, when preceded by a detected initial or name `initial_left`: An initial, when followed by a detected initial, name or interfix `naam_left`: Something that resembles a name, when followed by a name `naam_right`: Something that resembles a name, when preceded by a name `prefix_left`: A prefix, when followed by a prefix, initial, name or interfix |
|                 | eponymous_disease    | `docdeid.process.MultiTokenLookupAnnotator` | Lookup based on eponymous diseases, which will be tagged with `pseudo_name` and removed later (along with any overlap)                                                                                                                                                                                                                                                                                                                                                                                            |
| locations       | placename            | `docdeid.process.MultiTokenLookupAnnotator` | Lookup based on a compiled list of regions, provinces, municipalities and residences                                                                                                                                                                                                                                                                                                                                                                                                                              |
|                 | street_pattern       | `docdeid.process.RegexpAnnotator`           | Matches streetnames based on a pattern (ending in straat, plein, dam, etc.)                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|                 | street_lookup        | `docdeid.process.MultiTokenLookupAnnotator` | Lookup based on a list of streetnames from Basisadministratie Gemeenten                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|                 | housenumber          | `deduce.annotator.ContextAnnotator`         | Matches housenumber and housenumberletters, based on the following context patterns: `housenumber_right`: a 1-4 digit number, preceded by a streetname `housenumber_housenumberletter_right`: a 1-4 digit number and a single letter, preceded by a streetname `housenumberletter_right`: a single letter, preceded by a housenumber                                                                                                                                                                              |
|                 | postal_code          | `docdeid.process.RegexpAnnotator`           | Matches Dutch postal codes, i.e. four digits followed by two letters                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|                 | postbus              | `docdeid.process.RegexpAnnotator`           | Matches postbus, i.e. 'Postbus' followed by a 1-5 digit number, optionally with periods between them.                                                                                                                                                                                                                                                                                                                                                                                                             |
| institution     | hospital             | `docdeid.process.MultiTokenLookupAnnotator` | Lookup based on a list of hospitals.                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|                 | institution          | `docdeid.process.MultiTokenLookupAnnotator` | Lookup based on a list of healthcare institutions, based on Zorgkaart Nederland.                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| dates           | date_dmy_1           | `docdeid.process.RegexpAnnotator`           | Matches dates in dmy format, e.g. 01-01-2012                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|                 | date_dmy_2           | `docdeid.process.RegexpAnnotator`           | Matches dates in dmy format, e.g. 01 jan 2012                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|                 | date_ymd_1           | `docdeid.process.RegexpAnnotator`           | Matches dates in ymd format, e.g. 2012-01-01                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|                 | date_ymd_2           | `docdeid.process.RegexpAnnotator`           | Matches dates in ymd format, e.g. 2012 jan 01                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ages            | age                  | `deduce.annotator.RegexpPseudoAnnotator`    | Matches ages based on a number of digit patterns followed by jaar/jaar oud. Excludes matches that are preceded/followed by one of the `pre_pseudo` / `post_pseudo` words, e.g. 'sinds 10 jaar`                                                                                                                                                                                                                                                                                                                    |
| identifiers     | bsn                  | `deduce.annotator.BsnAnnotator`             | Matches Dutch social security numbers (BSN), based on a 9-digit pattern that also passes the 'elfproef'                                                                                                                                                                                                                                                                                                                                                                                                           |
|                 | identifier           | `docdeid.process.RegexpAnnotator`           | Matches any 7+ digit number as identifier                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| phone_numbers   | phone                | `deduce.annotator.PhoneNumberAnnotator`     | Matches phone numbers, based on regular expression pattern, optionally with a digit too few or a digit too much (common typos)                                                                                                                                                                                                                                                                                                                                                                                    |
| email_addresses | email                | `docdeid.process.RegexpAnnotator`           | Matches e-mail addresses, based on regular expression pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| urls            | url                  | `docdeid.process.RegexpAnnotator`           | Matches urls, based on regular expression pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

It's possible to add, remove, apply subsets, or to implement custom annotators, those options are described further down under [customizing `deduce`](#customizing-deduce). 

### Other processors

In addition to annotators, a `docdeid` de-identifier contains annotation processors, which do some operation to the set of annotations generated previously, and redactors, which take the annotation and replace them in the text. Other processors included in `deduce` are listed below:

| **Name**                    | **Group**       | **Description**                                                                                       |
|-----------------------------|-----------------|-------------------------------------------------------------------------------------------------------|
| person_annotation_converter | names           | Maps name tags to either PERSON or PATIENT, and removes overlap with 'pseudo_name'.                   |
| remove_street_tags          | locations       | Removes any matched street names that are not followed by a housenumber                               |
| clean_street_tags           | locations       | Cleans up street tags, e.g. straat+huisnummer -> locatie                                              |
| overlap_resolver            | post_processing | Makes sure overlap among annotations is resolved.                                                     |
| merge_adjacent_annotations  | post_processing | If there are any adjacent annotations with the same tag, they are merged into a single annotation.    |
| redactor                    | post_processing | Takes care of replacing the annotated PHIs with `[TAG]` (e.g. `[LOCATION-1]`, `[DATE-2]`)             |

### Lookup sets

In order to match tokens to known identifiable words or concepts, `deduce` has the following builtin lookup sets:

| **Name**               | **Size** | **Examples**                                                                           |
|------------------------|----------|----------------------------------------------------------------------------------------|
| prefix                 | 45       | bc., dhr., mijnheer 																	 | 
| initial                | 54       | Q, I, U 																				 |
| interfix               | 44       | van de, von, v/d 															  			 |
| first_name             | 14690    | Martin, Alco, Wieke 														  			 |
| interfix_surname       | 2384     | Rijke, Butter, Agtmaal 																 |
| surname                | 10346    | Kosters, Hilderink, Kogelman 															 |
| hospital               | 9283     | Oude en Nieuwe Gasthuis, sint Jans zkh., Dijklander 									 |
| hospital_abbr          | 21       | UMCG, WKZ, PMC 																		 |
| healthcare_institution | 244342   | Gezondheidscentrum Wesselerbrink, Fysiotherapie Heer, Ergotherapie Tilburg-Waalwyk eo. |
| placename              | 12049    | De Plaats, Diefdijk (U), Het Haantje (DR) 											 |
| street                 | 769569   | Ds. Van Diemenstraat, Jac. v den Eyndestr, Matenstr 									 |
| eponymous_disease      | 22512    | tumor van Brucellosis, Lobomycosis reactie, syndroom van Alagille 					 | 
| common_word            | 1008     | al, tuin, brengen 																	 |
| medical_term           | 6939     | bevattingsvermogen, iliacaal, oor 													 |
| stop_word              | 101      | kan, heb, dat 																		 |

## Customizing deduce

We highly recommend making some effort to customize `deduce`, as even some basic effort will almost surely increase accuracy. Below are outlined some ways to achieve this, including: making changes to the config, adding/removing custom pipeline components, and modifying the builtin lookup sets.

### Adding a custom config 

A default `base_config.json` ([source on GitHub](https://github.com/vmenger/deduce/blob/main/base_config.json)) file is packaged with `deduce`. Among with some basic settings, it defines all annotators (also listed above). Override settings, by providing an additional user config to Deduce, either as a file or as a dict: 

```python
from deduce import Deduce

deduce = Deduce(config='my_own_config.json')
deduce = Deduce(config={'redactor_open_char': '**', 'redactor_close_char': '**'})
```

This will only override settings that are explicitly set in the user config, all other settings are kept as is. If you want to add or delete annotators (e.g. changing regular expressions), it's easiest to make a copy of `base_config.json`, and load it as follows: 

```python
from deduce import Deduce

deduce = Deduce(load_base_config=False, config='my_own_config.json')
```

Note that you will now miss out on any updates to the base config that are packaged with new versions of Deduce. For that reason, a better way to add/remove processors is to [interact with `Deduce.processors` directly](#implementing-custom-components) after creating the model.

### Using `disabled` keyword to disable components

It's possible to disable specific (groups of) annotators or processors when deidentifying a text. For example, to apply all annotators, except those in the identifiers group: 

```python
from deduce import Deduce

deduce = Deduce()
deduce.deidentify(text, disabled={'identifiers'})
```

Or, to disable one specific date annotator in the dates group, but keeping the other date patterns:

```python
from deduce import Deduce

deduce = Deduce()
deduce.deidentify("text", disabled={'date_dmy_1'})
```

### Using `enabled` keyword

Although it's also possible to _enable_ only some processors, this is only useful in a limited amount of cases. You must manually specify the groups, individual annotators, and postprocessors to have a sensible output. For example, to de-identify only e-mail addresses, use:

```python
from deduce import Deduce

deduce = Deduce()
deduce.deidentify("text", enabled={
    'email-addresses', # annotator group, with annotators:
    'email', 
    'post_processing', # post processing group, with processors:
    'overlap_resolver',
    'merge_adjacent_annotations',
    'redactor'
})
```

The following example however will apply **no annotators**, as the `email` annotator is enabled, but its' group `email-addresses` is not: 

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

There might be a case where you want to add a custom annotator to `deduce` that requires its own tokenizing logic. Replacing the builtin tokenizer is not recommended, as builtin annotators depend on it, but it's possible to add more tokenizers as follows:

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

### Tailoring lookup structures

Updating the builtin lookup sets and tries is a very useful and straightforward way to tailor `deduce`. Changes can be made directly from the `Deduce.lookup_structs` attribute, as such: 

```python
from deduce import Deduce

deduce = Deduce()

# sets
deduce.lookup_structs['first_names'].add_items_from_iterable(["naam", "andere_naam"])
deduce.lookup_structs['whitelist'].add_items_from_iterable(["woord", "ander_woord"])

# tries
deduce.lookup_structs['residences'].add_items(["kleine", "plaats", "in", "de", "regio"])
deduce.lookup_structs['institutions'].add_items_from_iterable(["verzorgingstehuis", "hier", "om", "de", "hoek"])

```

Full documentation on sets and tries, and how to modify them, is available in the [docdeid API](https://docdeid.readthedocs.io/en/latest/api/docdeid.ds.html#docdeid.ds.lookup.LookupSet).

Larger changes may also be made by copying the source files and modifying them directly, by pointing `deduce` to the directory with modified sources:

```python
from deduce import Deduce

deduce = Deduce(lookup_data_path="/my/path")
```

It's important to copy the directory, or your changes will be overwritten with the next `deduce` update. Currently, there is no additional documentation available on how to structure and transform the lookup items in the directory, other than inspecting the pre-packaged files. Also remember that any updates to lookup values in next releases of Deduce will not be applied if `deduce` loads items from a copy, differences need to be tracked manually with each release.

### recall booster
For rule based systems the trade-off between precision and recall is a well known problem. In order to increase recall, `deduce` has a `recall_boost` option, which can be turned on in the `base_config.json` by setting `use_recall_boost` to `true`.  The resulting changes are listed in the table below.

| **Annotator** | **Change** |
| --- | --- |
| first_name_lookup | Matches also first names occurring in lowercase if they exceed the minimum length specified in the annotator config |
| surname_lookup | Matches also surnames occurring in lowercase if they exceed the minimum length specified in the annotator config |