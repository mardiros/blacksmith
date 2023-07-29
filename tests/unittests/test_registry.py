import pytest

import blacksmith
from blacksmith.domain import registry
from blacksmith.domain.exceptions import ConfigurationError, UnregisteredClientException
from blacksmith.domain.model import PathInfoField, PostBodyField, Request, Response
from blacksmith.domain.registry import Registry


def test_default_registry() -> None:
    class DummyRequest(Request):
        name: str = PathInfoField()

    class Dummy(Response):
        name: str

    default_registry = registry.registry = Registry()

    blacksmith.register(
        "dummies_api",
        "dummies",
        "api",
        "v5",
        path="/dummies/{name}",
        contract={
            "GET": (DummyRequest, Dummy),
        },
    )
    try:
        assert default_registry.client_service == {"dummies_api": ("api", "v5")}
        assert set(default_registry.clients.keys()) == {"dummies_api"}

        assert set(default_registry.clients["dummies_api"].keys()) == {"dummies"}

        api = default_registry.clients["dummies_api"]
        assert api["dummies"].resource is not None
        assert api["dummies"].resource.contract is not None
        assert api["dummies"].resource.path == "/dummies/{name}"
        assert set(api["dummies"].resource.contract.keys()) == {"GET"}
        assert api["dummies"].resource.contract["GET"][0] == DummyRequest
        assert api["dummies"].resource.contract["GET"][1] == Dummy
        assert api["dummies"].collection is None
    finally:
        # cleanup side effects
        from blacksmith.domain import registry as registry_module

        registry_module.registry = Registry()


def test_registry_without_collection() -> None:
    class DummyRequest(Request):
        name: str = PathInfoField()

    class Dummy(Response):
        name: str

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
    assert api["dummies"].resource is not None
    assert api["dummies"].resource.contract is not None
    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET"}
    assert api["dummies"].resource.contract["GET"][0] == DummyRequest
    assert api["dummies"].resource.contract["GET"][1] == Dummy
    assert api["dummies"].collection is None


def test_registry_without_response() -> None:
    class DummyRequest(Request):
        name: str = PathInfoField()

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
    assert api["dummies"].resource is not None
    assert api["dummies"].resource.contract is not None
    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET"}
    assert api["dummies"].resource.contract["GET"][0] == DummyRequest
    assert api["dummies"].resource.contract["GET"][1] is None


def test_registry_only_collection() -> None:
    class DummyRequest(Request):
        pass

    class Dummy(Response):
        name: str

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
    assert api["dummies"].collection is not None
    assert api["dummies"].collection.contract is not None
    assert api["dummies"].collection.path == "/dummies"
    assert set(api["dummies"].collection.contract.keys()) == {"GET"}
    assert api["dummies"].collection.contract["GET"][0] == DummyRequest
    assert api["dummies"].collection.contract["GET"][1] == Dummy
    assert api["dummies"].resource is None


def test_registry_complete() -> None:
    class CreateDummyRequest(Request):
        name: str = PostBodyField()

    class DummyRequest(Request):
        name: str = PathInfoField()

    class Dummy(Response):
        name: str

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
    assert api["dummies"].collection is not None
    assert api["dummies"].collection.contract is not None
    assert api["dummies"].collection.path == "/dummies"
    assert set(api["dummies"].collection.contract.keys()) == {"GET", "POST"}
    assert api["dummies"].collection.contract["GET"][0] == Request
    assert api["dummies"].collection.contract["GET"][1] == Dummy
    assert api["dummies"].collection.contract["POST"][0] == CreateDummyRequest
    assert api["dummies"].collection.contract["POST"][1] is None

    assert api["dummies"].resource is not None
    assert api["dummies"].resource.contract is not None
    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET", "DELETE"}
    assert api["dummies"].resource.contract["GET"][0] == DummyRequest
    assert api["dummies"].resource.contract["GET"][1] == Dummy
    assert api["dummies"].resource.contract["DELETE"][0] == DummyRequest
    assert api["dummies"].resource.contract["DELETE"][1] is None


def test_get_service() -> None:
    class DummyRequest(Request):
        pass

    class Dummy(Response):
        name: str

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


def test_registry_conflict() -> None:
    registry = Registry()
    registry.register(
        "client_name",
        "foo",
        "api",
        "v5",
        path="/foo/{name}",
        contract={
            "GET": (Request, None),
        },
    )

    with pytest.raises(ConfigurationError) as ctx:
        registry.register(
            "client_name",
            "bar",
            "api",
            "v6",
            path="/bar/{name}",
            contract={
                "GET": (Request, None),
            },
        )
    assert (
        str(ctx.value)
        == "Client client_name has been registered twice with api/v5 and api/v6"
    )
