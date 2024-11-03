import json
from textwrap import dedent
from typing import Any

import pytest
from fastapi.testclient import TestClient

from blacksmith.domain.model.http import HTTPResponse


@pytest.mark.parametrize(
    "params",
    [
        {
            "request": {"username": "naruto", "message": "Datte Bayo"},
            "blacksmith_responses": {
                "GET http://user.v1/users/naruto": HTTPResponse(
                    200,
                    {},
                    {
                        "email": "naruto@konoha.city",
                        "firstname": "Naruto",
                        "lastname": "Uzumaki",
                    },
                )
            },
            "expected_response": {"detail": "naruto@konoha.city accepted"},
            "expected_messages": [
                dedent(
                    """
                    Subject: notification
                    From: notification@localhost
                    To: "Naruto Uzumaki" <naruto@konoha.city>

                    Datte Bayo
                    """
                ).lstrip()
            ],
        }
    ],
)
def test_notif(params: dict[str, Any], client: TestClient, mboxes: list[str]):
    resp = client.post("/v1/notification", json=params["request"])
    assert json.loads(resp.content) == params["expected_response"]
    assert mboxes == params["expected_messages"]
