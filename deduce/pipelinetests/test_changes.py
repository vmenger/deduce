import difflib
import time
import unittest

import pandas as pd
from pandarallel import pandarallel
from pygit2 import Repository

pandarallel.initialize(nb_workers=6)

import deduce

SAMPLE_SIZE = 100

import logging

# Set Logger
logger = logging.getLogger("__name__")
logger.setLevel(logging.INFO)


def get_logging_filehandler(filename: str):
    handler = logging.FileHandler(filename, mode="w")
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


class TestChanges(unittest.TestCase):
    def setUp(self) -> None:

        self.version = "108"

        self.data = pd.read_csv(
            f"/Users/vmenger2/data/deduce-validate/pipeline_test/"
            f"deduce_ver_{self.version}_pipeline_test.csv"
        )

        self.data = self.data.fillna("")

        self.data = self.data.rename(
            columns={
                "text": "input_text",
                "text_annotated": "annotated_text_target",
                "text_deidentified": "deidentified_text_target",
            }
        )

    @staticmethod
    def annotator(row):

        # if 'input_text' not in row.columns:
        #     raise ValueError("Did not find input_text column in dataframe")

        try:

            annotated_text = deduce.annotate_text(
                text=row["input_text"],
                patient_first_names=row["first_names"],
                patient_initials=row["initials"],
                patient_surname=row["surname"],
                patient_given_name=row["given_name"],
            )

            row["annotated_text"] = annotated_text

        except Exception as e:

            row["annotated_text"] = str(e)

        return row

    @staticmethod
    def deidentifier(row):

        # if 'annotated_text' not in row.columns:
        #     raise ValueError("Did not find annotated_text column in dataframe")

        row["deidentified_text"] = deduce.deidentify_annotations(row["annotated_text"])

        return row

    def test_annotate_text_sample(self):
        self.test_annotate_text(SAMPLE_SIZE)

    def test_annotate_text(self, sample_size: int = None):

        test_data = self.data

        if sample_size is not None:

            if "bron" in test_data.columns:

                test_data = pd.concat(
                    [
                        group.sample(sample_size)
                        for _, group in test_data.groupby("bron")
                    ],
                    axis=0,
                )

            else:

                test_data = test_data.sample(sample_size)

        assert "input_text" in test_data.columns

        d = difflib.Differ()

        ann_handler = get_logging_filehandler("annotation_differences.log")
        dei_handler = get_logging_filehandler("deidentification_differences.log")

        logger.addHandler(ann_handler)
        logger.addHandler(dei_handler)

        branch_name = Repository("../").head.shorthand

        logger.info(
            f"Testing deduce version {deduce.__version__} on branch {branch_name} "
            f"against release {self.version}"
        )

        logger.info(f"Sample size = {sample_size}")

        logger.removeHandler(dei_handler)

        start = time.time()
        test_data = test_data.parallel_apply(self.annotator, axis=1)
        logger.info(f"Annotation took {(time.time() - start)/60:.1f} minutes")
        logger.info(150 * "#")

        num_annotation_differences = 0
        num_deidentification_differences = 0

        for _, row in test_data.iterrows():
            if row["annotated_text"] != row["annotated_text_target"]:

                num_annotation_differences += 1

                diff = d.compare(
                    row["annotated_text_target"].splitlines(),
                    row["annotated_text"].splitlines(),
                )

                logger.info(200 * "#")
                logger.info(f"Bron: {row['bron']}")
                logger.info("\n".join(diff))

        logger.removeHandler(ann_handler)
        logger.addHandler(dei_handler)

        # Deidentify
        start = time.time()
        test_data = test_data.parallel_apply(self.deidentifier, axis=1)
        logger.info(f"Deidentification took {(time.time() - start)/60:.1f} minutes")
        logger.info(150 * "#")

        for _, row in test_data.iterrows():

            if row["deidentified_text_target"] != row["deidentified_text"]:

                num_deidentification_differences += 1

                diff = d.compare(
                    row["deidentified_text"].splitlines(),
                    row["deidentified_text_target"].splitlines(),
                )
                logger.info(150 * "#")
                logger.info(f"Bron: {row['bron']}")
                logger.info("\n".join(diff))

        assert num_annotation_differences == 0
        assert num_deidentification_differences == 0
