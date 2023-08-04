import json

from docdeid import Annotation, AnnotationSet

from deduce import Deduce

model = Deduce()


class RegressionTester:
    def __init__(self, examples_file: str, enabled: set[str], known_failures: set[int]):
        self.examples_file = examples_file
        self.enabled = enabled
        self.known_failures = known_failures

    def run(self):

        with open(self.examples_file, "rb") as file:
            examples = json.load(file)["examples"]

        failures = set()

        for example in examples:

            trues = AnnotationSet(Annotation(**annotation) for annotation in example["annotations"])
            preds = model.deidentify(text=example["text"], enabled=self.enabled).annotations

            try:
                assert trues == preds
            except AssertionError:
                failures.add(example["example_id"])

        assert failures == self.known_failures


class TestRegression:
    def test_regression_url(self):
        RegressionTester(
            examples_file="data/urls.json",
            enabled={"urls", "url"},
            known_failures=set(),
        ).run()
