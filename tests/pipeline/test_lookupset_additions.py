def run_add_to_lookup_trie(model):
    example_dict = {
        "first_name": (["Lydia", "Soeroedjpersad", "Loua", "Ümmü", "Saâdia"]),
        "surname": ["Schoenmaker", "Schrijnewerkers", "Öcal", "Kayim"],
        "placename": ["Rotterdam", "Pangkalpinang", "Riga", "Caïro"],
    }

    for list_name, examples in example_dict.items():
        for i, example in enumerate(examples):
            sentence = f"data to anonymize is {example} in this sentence"
            result = model.deidentify(sentence)
            result_val = 1 if i == 0 else 0
            assert len(result.annotations) == result_val

        for example in examples:
            model.lookup_structs[list_name].add_item([example])
            assert [example] in model.lookup_structs[list_name]

    model.processors = model.annotator_loader.load(
        config=model.config, extras=model.annotator_load_extras
    )

    for list_name, examples in example_dict.items():
        for example in examples:
            result = model.deidentify(sentence)
            assert len(result.annotations) == 1


if __name__ == "__main__":
    from deduce.deduce import Deduce

    model = Deduce()
    run_add_to_lookup_trie(model)
