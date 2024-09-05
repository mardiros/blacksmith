import pytest

from blacksmith.domain.exceptions import UnregisteredServiceException
from blacksmith.sd._sync.adapters.consul import (
    ConsulApiError,
    Service,
    ServiceRequest,
    SyncConsulDiscovery,
    blacksmith_cli,
)
from blacksmith.sd._sync.adapters.nomad import SyncNomadDiscovery
from blacksmith.sd._sync.adapters.router import SyncRouterDiscovery
from blacksmith.sd._sync.adapters.static import SyncStaticDiscovery


def test_static_discovery(static_sd: SyncStaticDiscovery):
    endpoint = static_sd.get_endpoint("dummy", "v1")
    assert endpoint == "https://dummy.v1/"


def test_static_discovery_raise(static_sd: SyncStaticDiscovery):
    with pytest.raises(UnregisteredServiceException) as ctx:
        static_sd.get_endpoint("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"


def test_consul_sd_cli():
    cli = blacksmith_cli("http://consul:8888", "abc")
    assert cli.registry.client_service == {"consul": ("consul", "v1")}
    assert cli.registry.clients["consul"]["services"].collection is not None
    assert (
        cli.registry.clients["consul"]["services"].collection.path
        == "/catalog/service/{name}"
    )
    assert cli.registry.clients["consul"]["services"].collection.contract == {
        "GET": (ServiceRequest, Service)
    }


def test_consul_discovery_get_service_name(consul_sd: SyncConsulDiscovery):
    name = consul_sd.format_service_name("dummy-name", None)
    assert name == "dummy-name"

    name = consul_sd.format_service_name("dummy-name", "v42")
    assert name == "dummy-name-v42"


def test_consul_discovery_format_endoint(consul_sd: SyncConsulDiscovery):
    endpoint = consul_sd.format_endoint(None, "1.2.3.4", 8080)
    assert endpoint == "http://1.2.3.4:8080"

    endpoint = consul_sd.format_endoint("v42", "1.2.3.4", 8080)
    assert endpoint == "http://1.2.3.4:8080/v42"


def test_consul_discovery_get_endpoint(consul_sd: SyncConsulDiscovery):
    endpoint = consul_sd.get_endpoint("dummy", "v1")
    assert endpoint == "http://8.8.8.8:1234/v1"


def test_consul_discovery_resolve(consul_sd: SyncConsulDiscovery):
    service = consul_sd.resolve("dummy", "v1")
    assert service == Service(
        Address="1.1.1.1", ServiceAddress="8.8.8.8", ServicePort=1234
    )


def test_consul_discovery_resolve_unversionned_endpoint(
    consul_sd: SyncConsulDiscovery,
):
    service = consul_sd.resolve("dummy", None)
    assert service == Service(
        Address="1.1.1.1", ServiceAddress="8.8.8.8", ServicePort=1234
    )


@pytest.mark.parametrize(
    "body",
    [
        {
            "Address": "2.2.2.2",
            "ServiceAddress": "1.1.1.1",
            "ServicePort": 1234,
        },
        {
            "Address": "1.1.1.1",
            "ServiceAddress": "",
            "ServicePort": 1234,
        },
        {
            "Address": "1.1.1.1",
            "ServicePort": 1234,
        },
        {
            "Address": "1.1.1.1",
            "ServiceAddress": None,
            "ServicePort": 1234,
        },
    ],
)
def test_consul_discovery_resolve_address(
    consul_sd_with_body: SyncConsulDiscovery,
):
    service = consul_sd_with_body.resolve("dummy", None)
    assert service.address == "1.1.1.1"


def test_consul_discovery_resolve_unregistered(consul_sd: SyncConsulDiscovery):
    with pytest.raises(UnregisteredServiceException) as ctx:
        consul_sd.resolve("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"


def test_consul_discovery_get_unversionned_endpoint(
    consul_sd: SyncConsulDiscovery,
):
    endpoint = consul_sd.get_endpoint("dummy", None)
    assert endpoint == "http://8.8.8.8:1234"


def test_consul_discovery_get_endpoint_unregistered(
    consul_sd: SyncConsulDiscovery,
):
    with pytest.raises(UnregisteredServiceException) as ctx:
        consul_sd.get_endpoint("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"


def test_consul_resolve_consul_error(consul_sd: SyncConsulDiscovery):
    with pytest.raises(ConsulApiError) as ctx:
        consul_sd.resolve("dummy", "v3")
    assert str(ctx.value) == "422 Unprocessable entity"


def test_nomad_resolve(nomad_sd: SyncNomadDiscovery, monkeypatch):
    monkeypatch.setenv("NOMAD_UPSTREAM_ADDR_dummy", "127.0.0.1:8000")
    endpoint: str = nomad_sd.get_endpoint("dummy", "v1")
    assert endpoint == "http://127.0.0.1:8000"


def test_router_sd_get_endpoint_versionned(router_sd: SyncRouterDiscovery):
    endpoint = router_sd.get_endpoint("dummy", "v1")
    assert endpoint == "http://router/dummy-v1/v1"


def test_router_sd_get_endpoint_unversionned(router_sd: SyncRouterDiscovery):
    endpoint = router_sd.get_endpoint("dummy", None)
    assert endpoint == "http://router/dummy"
