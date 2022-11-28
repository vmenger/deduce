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

print(doc.deidentifed_text)
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

Previously, the `annotate_text` function offered disabling specific categories by using `dates`, `ages`, `names`, etc. keywords. This behaviour can be achieved by setting the `annotators_disabled` argument of the `Deduce.deidentify` method. Note that the identification logic of Deduce is now further split up into `Annotator` classes, allowing disabling/enabling specific components. You can read more about the specific annotators and other components in the tutorial [here](tutorial.md#annotators), and more information on enabling, disabling, replacing or modifying specific components [here](tutorial.md#customizing-deduce).


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
    processors_disabled={'dates', 'ages'}
)   
```

</td>
</tr>
</table>