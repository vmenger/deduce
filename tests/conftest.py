import pytest

from deduce import Deduce


@pytest.fixture(scope="session")
def model():
    return Deduce(build_lookup_structs=True)
