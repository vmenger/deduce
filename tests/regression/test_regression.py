import json
from typing import Optional

from docdeid import Annotation, AnnotationSet


def regression_test(
    model,
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
        trues = AnnotationSet(
            Annotation(**annotation) for annotation in example["annotations"]
        )
        preds = model.deidentify(text=example["text"], enabled=enabled).annotations

        try:
            assert trues == preds
        except AssertionError:
            failures.add(example["id"])

    assert failures == known_failures


class TestRegression:
    def test_regression_name(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/names.json",
            enabled={
                "names",
                "prefix_with_initial",
                "prefix_with_name",
                "interfix_with_name",
                "initial_with_capital",
                "initial_interfix",
                "first_name_lookup",
                "surname_lookup",
                "person_first_name",
                "person_initial_from_name",
                "person_initials",
                "person_surname",
                "name_context",
                "person_annotation_converter",
            },
        )

    def test_regression_location(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/locations.json",
            enabled={
                "locations",
                "placename",
                "street_pattern",
                "street_lookup",
                "housenumber",
                "postal_code",
                "postbus",
                "remove_street_tags",
                "clean_street_tags",
            },
        )

    def test_regression_institution(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/institutions.json",
            enabled={
                "institutions",
                "hospital",
                "institution",
            },
        )

    def test_regression_date(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/dates.json",
            enabled={"dates", "date_dmy_1", "date_dmy_2", "date_ymd_1", "date_ymd_2"},
        )

    def test_regression_age(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/ages.json",
            enabled={"ages", "age"},
        )

    def test_regression_identifier(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/identifiers.json",
            enabled={"identifiers", "bsn", "identifier"},
        )

    def test_regression_phone(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/phone_numbers.json",
            enabled={"phone_numbers", "phone"},
        )

    def test_regression_email(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/emails.json",
            enabled={"email_addresses", "email"},
        )

    def test_regression_url(self, model):
        regression_test(
            model=model,
            examples_file="tests/regression/data/urls.json",
            enabled={"urls", "url"},
        )
