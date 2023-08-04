import json

from docdeid import Annotation, AnnotationSet

from deduce import Deduce

model = Deduce()


def regression_test(examples_file: str, enabled: set[str], known_failures: set[int]):

    with open(examples_file, "rb") as file:
        examples = json.load(file)["examples"]

    failures = set()

    for example in examples:

        trues = AnnotationSet(Annotation(**annotation) for annotation in example["annotations"])
        preds = model.deidentify(text=example["text"], enabled=enabled).annotations

        try:
            assert trues == preds
        except AssertionError:
            failures.add(example["example_id"])

    assert failures == known_failures


class TestRegression:
    def test_regression_phone(self):

        regression_test(
            examples_file="tests/regression/data/phone_numbers.json",
            enabled={"phone_numbers", "phone"},
            known_failures=set(),
        )

    def test_regression_email(self):

        regression_test(
            examples_file="tests/regression/data/emails.json",
            enabled={"email_addresses", "email"},
            known_failures=set(),
        )

    def test_regression_url(self):

        regression_test(
            examples_file="tests/regression/data/urls.json",
            enabled={"urls", "url"},
            known_failures=set(),
        )
