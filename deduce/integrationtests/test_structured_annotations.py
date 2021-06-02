import pandas as pd

import deduce


def get_annotations(raw_text: str) -> bool:
    annotations = deduce.annotate_text_structured(raw_text)
    for annotation in annotations:
        if annotation.end_ix - annotation.start_ix != len(annotation.text_):
            return False
        original = raw_text[annotation.start_ix:annotation.end_ix].replace("<", "(").replace(">", ")")
        if original != annotation.text_ and (annotation.tag != "INSTELLING" or original.lower() != annotation.text_):
            return False
    return True

def test_get_annotations(texts_list: list) -> bool:
    return all([get_annotations(text) for text in texts_list])

if __name__ == "__main__":
    filename = '/media/bigdata/2. Gebruik en toepassing van data/20_12_18_Pablo_Mosteiro_Anonymization/raw_texts/merged.csv'
    df = pd.read_csv(filename, sep=";")
    texts = df.Tekst.tolist()
    assert test_get_annotations(texts)
    print("OK")
