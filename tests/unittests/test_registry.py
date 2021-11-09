import pytest
from aioli.domain.exceptions import (
    UnregisteredClientException,
)

from aioli.domain.model import Request, PathInfoField, PostBodyField, Response
from aioli.domain.registry import Registry


def test_registry_without_collection():
    class DummyRequest(Request):
        name = PathInfoField(str)

    class Dummy(Response):
        name = str

    registry = Registry()
    registry.register(
        "dummies_api",
        "dummies",
        "api",
        "v5",
        path="/dummies/{name}",
        contract={
            "GET": (DummyRequest, Dummy),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET"}
    assert api["dummies"].resource.contract["GET"][0] == DummyRequest
    assert api["dummies"].resource.contract["GET"][1] == Dummy
    assert api["dummies"].collection is None


def test_registry_without_response():
    class DummyRequest(Request):
        name = PathInfoField(str)

    registry = Registry()
    registry.register(
        "dummies_api",
        "dummies",
        "api",
        "v5",
        path="/dummies/{name}",
        contract={
            "GET": (DummyRequest, None),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET"}
    assert api["dummies"].resource.contract["GET"][0] == DummyRequest
    assert api["dummies"].resource.contract["GET"][1] == None


def test_registry_only_collection():
    class DummyRequest(Request):
        pass

    class Dummy(Response):
        name = str

    registry = Registry()
    registry.register(
        "dummies_api",
        "dummies",
        "api",
        "v5",
        collection_path="/dummies",
        collection_contract={
            "GET": (DummyRequest, Dummy),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].collection.path == "/dummies"
    assert set(api["dummies"].collection.contract.keys()) == {"GET"}
    assert api["dummies"].collection.contract["GET"][0] == DummyRequest
    assert api["dummies"].collection.contract["GET"][1] == Dummy
    assert api["dummies"].resource is None


def test_registry_complete():
    class CreateDummyRequest(Request):
        name = PostBodyField(str)

    class DummyRequest(Request):
        name = PathInfoField(str)

    class Dummy(Response):
        name = str

    registry = Registry()
    registry.register(
        "dummies_api",
        "dummies",
        "api",
        "v5",
        path="/dummies/{name}",
        contract={
            "GET": (DummyRequest, Dummy),
            "DELETE": (DummyRequest, None),
        },
        collection_path="/dummies",
        collection_contract={
            "POST": (CreateDummyRequest, None),
            "GET": (Request, Dummy),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].collection.path == "/dummies"
    assert set(api["dummies"].collection.contract.keys()) == {"GET", "POST"}
    assert api["dummies"].collection.contract["GET"][0] == Request
    assert api["dummies"].collection.contract["GET"][1] == Dummy
    assert api["dummies"].collection.contract["POST"][0] == CreateDummyRequest
    assert api["dummies"].collection.contract["POST"][1] == None

    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET", "DELETE"}
    assert api["dummies"].resource.contract["GET"][0] == DummyRequest
    assert api["dummies"].resource.contract["GET"][1] == Dummy
    assert api["dummies"].resource.contract["DELETE"][0] == DummyRequest
    assert api["dummies"].resource.contract["DELETE"][1] is None


def test_get_service():
    class DummyRequest(Request):
        pass

    class Dummy(Response):
        name = str

    registry = Registry()
    registry.register(
        "dummies_api",
        "dummies",
        "api",
        "v5",
        collection_path="/dummies",
        collection_contract={
            "GET": (DummyRequest, Dummy),
        },
    )

    srv, resources = registry.get_service("dummies_api")
    assert srv == registry.client_service["dummies_api"]
    assert resources == registry.clients["dummies_api"]

    with pytest.raises(UnregisteredClientException) as ctx:
        registry.get_service("DUMMIES_API")

    assert str(ctx.value) == "Unregistered client 'DUMMIES_API'"
