
if __name__ == '__main__':

    from deduce.deduce import deduce

    doc = deduce.deidentify(text="Pieter", annotators_enabled=['dates'])

    print(doc.text)
    print(doc.annotations)
    print(doc.deidentified_text)
