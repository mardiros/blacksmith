import pytest
from aioli.sd.adapters import StaticDiscovery

@pytest.fixture
def static_sd():
    dummy_endpoints = {("dummy", "v1"): "https://dummy.v1/"}
    return StaticDiscovery(dummy_endpoints)
