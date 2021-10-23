from aioli.domain.registry import Registry
from aioli.domain.model import Params, PathInfoField, PostBodyField, Response


def test_registry_without_collection():
    class DummyParams(Params):
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
            "GET": (DummyParams, Dummy),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET"}
    assert api["dummies"].resource.contract["GET"][0] == DummyParams
    assert api["dummies"].resource.contract["GET"][1] == Dummy
    assert api["dummies"].collection is None

def test_registry_without_response():
    class DummyParams(Params):
        name = PathInfoField(str)

    registry = Registry()
    registry.register(
        "dummies_api",
        "dummies",
        "api",
        "v5",
        path="/dummies/{name}",
        contract={
            "GET": (DummyParams, None),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET"}
    assert api["dummies"].resource.contract["GET"][0] == DummyParams
    assert api["dummies"].resource.contract["GET"][1] == None


def test_registry_only_collection():
    class DummyParams(Params):
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
            "GET": (DummyParams, Dummy),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].collection.path == "/dummies"
    assert set(api["dummies"].collection.contract.keys()) == {"GET"}
    assert api["dummies"].collection.contract["GET"][0] == DummyParams
    assert api["dummies"].collection.contract["GET"][1] == Dummy
    assert api["dummies"].resource is None



def test_registry_complete():

    class CreateDummyParams(Params):
        name = PostBodyField(str)

    class DummyParams(Params):
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
            "GET": (DummyParams, Dummy),
            "DELETE": (DummyParams, None),
        },
        collection_path="/dummies",
        collection_contract={
            "POST": (CreateDummyParams, None),
            "GET": (Params, Dummy),
        },
    )

    assert registry.client_service == {"dummies_api": ("api", "v5")}
    assert set(registry.clients.keys()) == {"dummies_api"}

    assert set(registry.clients["dummies_api"].keys()) == {"dummies"}

    api = registry.clients["dummies_api"]
    assert api["dummies"].collection.path == "/dummies"
    assert set(api["dummies"].collection.contract.keys()) == {"GET", "POST"}
    assert api["dummies"].collection.contract["GET"][0] == Params
    assert api["dummies"].collection.contract["GET"][1] == Dummy
    assert api["dummies"].collection.contract["POST"][0] == CreateDummyParams
    assert api["dummies"].collection.contract["POST"][1] == None

    assert api["dummies"].resource.path == "/dummies/{name}"
    assert set(api["dummies"].resource.contract.keys()) == {"GET", "DELETE"}
    assert api["dummies"].resource.contract["GET"][0] == DummyParams
    assert api["dummies"].resource.contract["GET"][1] == Dummy
    assert api["dummies"].resource.contract["DELETE"][0] == DummyParams
    assert api["dummies"].resource.contract["DELETE"][1] is None
