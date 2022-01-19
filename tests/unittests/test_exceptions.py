import pytest

from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse


@pytest.mark.parametrize("status_code", [400, 401, 422, 499])
def test_http_4xx_error(status_code: int, dummy_http_request: HTTPRequest):
    err = HTTPError("test", dummy_http_request, HTTPResponse(status_code, {}, {}))
    assert err.is_client_error is True
    assert err.is_server_error is False


@pytest.mark.parametrize("status_code", [500, 503, 599])
def test_http_5xx_error(status_code: int, dummy_http_request: HTTPRequest):
    err = HTTPError("test", dummy_http_request, HTTPResponse(status_code, {}, {}))
    assert err.is_client_error is False
    assert err.is_server_error is True
