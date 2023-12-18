# Migrating to version `3.0.0`

Version `3.0.0` of `deduce` includes many optimizations that allow more accurate de-identification, some already included in `2.1.0` - `2.5.0.` It also includes some structural optimizations. Version `3.0.0` should be backwards compatible, but some functionality is scheduled for removal in `3.1.0`. Those changes are listed below.

## Custom config

Adding a custom config is now possible as a `dict` or as a filename pointing to a `json`. Both should be presented to `deduce` with the `config` keyword, e.g.:

```python
deduce = Deduce(config='my_own_config.json')
deduce = Deduce(config={'redactor_open_char': '**', 'redactor_close_char': '**'})
```

The `config_file` keyword is no longer used, please use `config` instead.

## Lookup structure names

For consistency, lookup structures are now all named after the singular form:

| **Old name**            | **New name**           |
|-------------------------|------------------------|
| prefixes                | prefix                 |
| first_names             | first_name             |
| interfixes              | interfixes             |
| interfix_surnames       | interfix_surname       |
| surnames                | surname                |
| streets                 | street                 |
| placenames              | placename              |
| hospitals               | hospital               |
| healthcare_institutions | healthcare_institution |

Additionally, the `first_name_exceptions` and `surname_exceptions` list are deprecated. The exception items are now simply removed from the list in a more structured way, so there is no need to explicitly filter exceptions in patterns, etc.

## The `annotator_type` field in config

In a config, the `annotator_type` should be specified for each annotator, so `Deduce` knows what annotator to load. In `3.0.0` we simplified this a bit. In most cases, the `annotator_type` field should be set to `module.Class` of the annotator that should be loaded, and `Deduce` will handle the rest (sometimes with a little bit of magic, so all arguments are presented with the right type). You should make the following changes:

| **`annotator_type`** | **Change**                                                                                                                                                                                                                                                                                                                                           |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `multi_token`        | `docdeid.process.MultiTokenLookupAnnotator`                                                                                                                                                                                                                                                                                                          |
| `dd_token_pattern`   | This used to load `docdeid.process.TokenPatternAnnotator`, but this is now replaced by `deduce.annotator.TokenPatternAnnotator`. The latter is more poweful, but needs a different pattern. A `docdeid.process.TokenPatternAnnotator` can no longer be loaded through config, although adding it manually to `Deduce.processors` is always possible. |
| `token_pattern`      | `deduce.annotator.TokenPatternAnnotator`                                                                                                                                                                                                                                                                                                             |
| `annotation_context` | `deduce.annotator.ContextAnnotator`                                                                                                                                                                                                                                                                                                                  |
| `custom`             | Use `module.Class` directly, where `module` and `class` fields used to be specified in `args`. They should be removed there.                                                                                                                                                                                                                         |
| `regexp`             | `docdeid.process.RegexpAnnotator`                                                                                                                                                                                                                                                                                                                    |



# Migrating to version `2.0.0`

Version `2.0.0` of `deduce` sees a major refactor that enables speedup, configuration, customization, and more. With it, the interface to apply `deduce` to text changes slightly. Updating your code to the new interface should not take more than a few minutes. The details are outlined below.

## Calling `deduce`

`deduce` is now called from `Deduce.deidentify`, which replaces the `annotate_text` and `deidentify_annotations` functions. Those functions will give a `DeprecationWarning` from version `2.0.0`, and will be deprecated from version `2.1.0`. 

<table>
<tr>
<th align="center" width="50%">deprecated</th>
<th align="center" width="50%">new</th>
</tr>
<tr>
<td>

```python
from deduce import annotate_text, deidentify_annotations

text = "Jan Jansen"

annotated_text = annotate_text(text)
deidentified_text = deidentify_annotations(annotated_text)
```

</td>
<td>

```python
from deduce import Deduce

text = "Jan Jansen"

deduce = Deduce()
doc = deduce.deidentify(text)   
```

</td>
</tr>
</table>

## Accessing output

The annotations and deidentified text are now available in the `Document` object. Intext annotations can still be useful for comparisons, they can be obtained by passing the document to a util function from the `docdeid` library (note that the format has changed). 

<table>
<tr>
<th align="center" width="50%">deprecated</th>
<th align="center" width="50%">new</th>
</tr>
<tr>
<td>

```python
print(annotated_text)
'<PERSOON Jan Jansen>'

print(deidentified_text)
'<PERSOON-1>'
```

</td>
<td>

```python
import docdeid as dd

print(dd.utils.annotate_intext(doc))
'<PERSOON>Jan Jansen</PERSOON>'

print(doc.annotations)
AnnotationSet({
    Annotation(
        text="Jan Jansen", 
        start_char=0, 
        end_char=10, 
        tag="persoon", 
        length="10"
    )
})

print(doc.deidentified_text)
'<PERSOON-1>'
```

</td>
</tr>
</table>

## Adding patient names

The `patient_first_names`, `patient_initials`, `patient_surname` and `patient_given_name` keywords of `annotate_text` are replaced with a structured way to enter this information, in the `Person` class. This class can be passed to `deidentify()` as metadata. The use of a given name is deprecated, it can instead be added as a separate first name. The behaviour is still the same.

<table>
<tr>
<th align="center" width="50%">deprecated</th>
<th align="center" width="50%">new</th>
</tr>
<tr>
<td>

```python
from deduce import annotate_text, deidentify_annotations

text = "Jan Jansen"

annotated_text = annotate_text(
    text, 
    patient_first_names="Jan Hendrik", 
    patient_initials="JH", 
    patient_surname="Jansen", 
    patient_given_name="Joop"
)
deidentified_text = deidentify_annotations(annotated_text)
```

</td>
<td>

```python
from deduce import Deduce
from deduce.person import Person

text = "Jan Jansen"
patient = Person(
    first_names=['Jan', 'Hendrik', 'Joop'], 
    initials="JH", 
    surname="Jansen"
)

deduce = Deduce()
doc = deduce.deidentify(text, metadata={'patient': patient})   
```

</td>
</tr>
</table>

## Enabling/disabling specific categories

Previously, the `annotate_text` function offered disabling specific categories by using `dates`, `ages`, `names`, etc. keywords. This behaviour can be achieved by setting the `disabled` argument of the `Deduce.deidentify` method. Note that the identification logic of Deduce is now further split up into `Annotator` classes, allowing disabling/enabling specific components. You can read more about the specific annotators and other components in the tutorial [here](tutorial.md#annotators), and more information on enabling, disabling, replacing or modifying specific components [here](tutorial.md#customizing-deduce).


<table>
<tr>
<th align="center" width="50%">deprecated</th>
<th align="center" width="50%">new</th>
</tr>
<tr>
<td>

```python
from deduce import annotate_text, deidentify_annotations

text = "Jan Jansen"

annotated_text = annotate_text(
    text,
    dates=False,
    ages=False
)
deidentified_text = deidentify_annotations(annotated_text)
```

</td>
<td>

```python
from deduce import Deduce

text = "Jan Jansen"

deduce = Deduce()
doc = deduce.deidentify(
    text, 
    disabled={'dates', 'ages'}
)   
```

</td>
</tr>
</table>
