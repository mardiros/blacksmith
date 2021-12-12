import pytest

from aioli.domain.exceptions import HTTPError
from aioli.domain.model.http import HTTPResponse


@pytest.mark.parametrize("status_code", [400, 401, 422, 499])
def test_http_4xx_error(status_code, dummy_http_request):
    err = HTTPError("test", dummy_http_request, HTTPResponse(status_code, {}, {}))
    assert err.is_client_error is True
    assert err.is_server_error is False


@pytest.mark.parametrize("status_code", [500, 503, 599])
def test_http_5xx_error(status_code, dummy_http_request):
    err = HTTPError("test", dummy_http_request, HTTPResponse(status_code, {}, {}))
    assert err.is_client_error is False
    assert err.is_server_error is True