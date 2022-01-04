import pytest

from blacksmith.domain.model import HTTPRequest


@pytest.fixture
def dummy_http_request():
    return HTTPRequest(
        "/dummy/{name}",
        {"name": 42},
        {"foo": "bar"},
        {"X-Req-Id": "42"},
        '{"bandi_manchot": "777"}',
    )
