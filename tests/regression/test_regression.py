import json
from typing import Optional

from docdeid import Annotation, AnnotationSet

from deduce import Deduce


def regression_test(
    model: Deduce,
    examples_file: str,
    enabled: set[str],
    known_failures: Optional[set[int]] = None,
):
    if known_failures is None:
        known_failures = set()

    with open(examples_file, "rb") as file:
        examples = json.load(file)["examples"]

    failures = set()

    for example in examples:
        add_recall_booster_annotations(example, model)

        if example["id"] == 112:
            x = 2

        trues = AnnotationSet(
            Annotation(**annotation) for annotation in example["annotations"]
        )

        preds = model.deidentify(text=example["text"], enabled=enabled).annotations

        try:
            assert trues == preds
        except AssertionError:
            print(preds)
            failures.add(example["id"])

    assert failures == known_failures


def add_recall_booster_annotations(example, model):
    if not model.config["use_recall_boost"]:
        return
    recall_booster_annotations = example.get("recall_booster_annotations", [])
    example["annotations"] += recall_booster_annotations
    example["annotations"].sort(key=lambda x: x["start_char"])


def annotators_from_group(model: Deduce, group: str) -> set[str]:
    return {name for name, _ in model.processors[group]}.union({group})


class TestRegression:
    def test_regression_name(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/names.json",
            enabled=annotators_from_group(model, "names"),
        )

    def test_regression_name_patient_environment(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/names_patient_environment.json",
            enabled=annotators_from_group(model, "names"),
        )

    def test_regression_location(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/locations.json",
            enabled=annotators_from_group(model, "locations"),
        )

    def test_regression_institution(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/institutions.json",
            enabled=annotators_from_group(model, "institutions"),
        )

    def test_regression_date(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/dates.json",
            enabled=annotators_from_group(model, "dates"),
        )

    def test_regression_date_recall_booster(self, model_with_recall_boost):
        regression_test(
            model=model_with_recall_boost,
            examples_file="tests/data/regression_cases/dates.json",
            enabled=annotators_from_group(model_with_recall_boost, "dates"),
        )

    def test_regression_age(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/ages.json",
            enabled=annotators_from_group(model, "ages"),
        )

    def test_regression_identifier(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/identifiers.json",
            enabled=annotators_from_group(model, "identifiers"),
        )

    def test_regression_phone(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/phone_numbers.json",
            enabled=annotators_from_group(model, "phone_numbers"),
        )

    def test_regression_email(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/emails.json",
            enabled=annotators_from_group(model, "email_addresses"),
        )

    def test_regression_url(self, model):
        regression_test(
            model=model,
            examples_file="tests/data/regression_cases/urls.json",
            enabled=annotators_from_group(model, "urls"),
        )
