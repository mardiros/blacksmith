import pytest
import json

from fastapi.testclient import TestClient
from blacksmith.domain.model.http import HTTPResponse

from notif.views import fastapi
from notif.config import AppConfig


@pytest.mark.parametrize("params", [
    {
        "request": {"username": "naruto", "message": "Datte Bayo"},
        "blacksmith_responses": {
            "GET http://user.v1/users/naruto": HTTPResponse(200, {}, {
                "email": "naruto@konoha.city",
                "firstname": "Naruto",
                "lastname": "Uzumaki",
            })
        },
        "expected": {'detail': 'naruto@konoha.city accepted'},
    }
])
@pytest.mark.asyncio
def test_notif(params, client: TestClient):
    resp = client.post("/v1/notification", json=params["request"])
    assert json.loads(resp.content) == params["expected"]

