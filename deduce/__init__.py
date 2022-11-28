import importlib.metadata

from deduce.deduce import (
    Deduce,
    annotate_text,
    annotate_text_structured,
    deidentify_annotations,
)

__version__ = importlib.metadata.version(__package__ or __name__)
