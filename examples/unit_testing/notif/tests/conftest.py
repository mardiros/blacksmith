from email.message import Message
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from notif.config import FastConfig
from notif.emailing import AbstractEmailSender
from notif.views import fastapi

from blacksmith import (
    AsyncAbstractTransport,
    AsyncRouterDiscovery,
    HTTPRequest,
    HTTPResponse,
    HTTPTimeout,
)


class FakeTransport(AsyncAbstractTransport):
    def __init__(self, responses: dict[str, HTTPResponse]):
        super().__init__()
        self.responses = responses

    async def __call__(
        self,
        req: HTTPRequest,
        client_name: str,
        path: str,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        """This is the next function of the middleware."""
        return self.responses[f"{req.method} {req.url}"]


class Mailboxes:
    boxes: ClassVar[list[str]] = []


class FakeEmailSender(AbstractEmailSender):
    async def sendmail(self, addr: str, port: int, message: Message):
        Mailboxes.boxes.append(message.as_string())

    async def get_endpoint(self) -> tuple[str, int]:
        return "smtp", 25


@pytest.fixture
def settings():
    return {
        "service_url_fmt": "http://{service}.{version}",
        "unversioned_service_url_fmt": "http://{service}",
        "email_sender": FakeEmailSender(),
    }


@pytest.fixture
async def configure_dependency_injection(params, settings):
    settings["transport"] = FakeTransport(params["blacksmith_responses"])
    settings["sd"] = AsyncRouterDiscovery(
        settings["service_url_fmt"],
        settings["unversioned_service_url_fmt"],
    )
    await FastConfig.configure(settings)


@pytest.fixture
def client(configure_dependency_injection):
    client = TestClient(fastapi)
    yield client


@pytest.fixture
def mboxes():
    Mailboxes.boxes.clear()
    yield Mailboxes.boxes
    Mailboxes.boxes.clear()
