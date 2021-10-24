import pytest

from aioli.sd.adapters import StaticDiscovery
from aioli.sd.adapters.static import Endpoints


@pytest.fixture
def static_sd():
    dummy_endpoints: Endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return StaticDiscovery(dummy_endpoints)
