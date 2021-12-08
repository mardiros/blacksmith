import aioli

from .scanned_resources import registry


def test_scan():
    assert registry.client_service == {}
    aioli.scan("tests.unittests.scanned_resources")
    assert registry.client_service == {"api": ("vegetables", "v1")}
