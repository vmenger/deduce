import pytest
from frozendict import frozendict

from deduce import Deduce


@pytest.fixture(scope="session")
def model():
    return Deduce(build_lookup_structs=False)


@pytest.fixture(scope="session")
def model_with_recall_boost():
    config = Deduce._initialize_config()
    config = dict(config)
    config["use_recall_boost"] = True
    config = frozendict(config)
    return Deduce(build_lookup_structs=False, config=config, load_base_config=False)
