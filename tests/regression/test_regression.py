import json
from typing import Optional

import pytest
from docdeid import Annotation, AnnotationSet

from deduce import Deduce


@pytest.fixture
def model(shared_datadir):
    # FIXME Sorry, due to the design decision of pytest-datadir to create a new copy
    #   of `shared_datadir` for every test, we cannot reuse this fixture
    #   for all tests in this module or package.
    return Deduce(
        build_lookup_structs=True,
        save_lookup_structs=False,
        lookup_data_path=shared_datadir / "lookup",
    )


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
        trues = AnnotationSet(
            Annotation(**annotation) for annotation in example["annotations"]
        )
        preds = model.deidentify(text=example["text"], enabled=enabled).annotations

        try:
            assert trues == preds
        except AssertionError:
            failures.add(example["id"])

    assert failures == known_failures


def annotators_from_group(model: Deduce, group: str) -> set[str]:
    return {name for name, _ in model.processors[group]}.union({group})


class TestRegression:
    def test_regression_name(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "names.json",
            enabled=annotators_from_group(model, "names"),
        )

    def test_regression_location(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "locations.json",
            enabled=annotators_from_group(model, "locations"),
        )

    def test_regression_institution(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "institutions.json",
            enabled=annotators_from_group(model, "institutions"),
        )

    def test_regression_date(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "dates.json",
            enabled=annotators_from_group(model, "dates"),
        )

    def test_regression_age(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "ages.json",
            enabled=annotators_from_group(model, "ages"),
        )

    def test_regression_identifier(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "identifiers.json",
            enabled=annotators_from_group(model, "identifiers"),
        )

    def test_regression_phone(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "phone_numbers.json",
            enabled=annotators_from_group(model, "phone_numbers"),
        )

    def test_regression_email(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "emails.json",
            enabled=annotators_from_group(model, "email_addresses"),
        )

    def test_regression_url(self, model, shared_datadir):
        regression_test(
            model=model,
            examples_file=shared_datadir / "urls.json",
            enabled=annotators_from_group(model, "urls"),
        )
