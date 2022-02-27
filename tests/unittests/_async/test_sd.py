import pytest

from blacksmith.domain.exceptions import UnregisteredServiceException
from blacksmith.sd._async.adapters.consul import (
    AsyncConsulDiscovery,
    ConsulApiError,
    Service,
    ServiceRequest,
    blacksmith_cli,
)
from blacksmith.sd._async.adapters.router import AsyncRouterDiscovery
from blacksmith.sd._async.adapters.static import AsyncStaticDiscovery


async def test_static_discovery(static_sd: AsyncStaticDiscovery):
    endpoint = await static_sd.get_endpoint("dummy", "v1")
    assert endpoint == "https://dummy.v1/"


async def test_static_discovery_raise(static_sd: AsyncStaticDiscovery):
    with pytest.raises(UnregisteredServiceException) as ctx:
        await static_sd.get_endpoint("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"


async def test_consul_sd_cli():
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


async def test_consul_discovery_get_service_name(consul_sd: AsyncConsulDiscovery):
    name = consul_sd.format_service_name("dummy-name", None)
    assert name == "dummy-name"

    name = consul_sd.format_service_name("dummy-name", "v42")
    assert name == "dummy-name-v42"


async def test_consul_discovery_format_endoint(consul_sd: AsyncConsulDiscovery):
    endpoint = consul_sd.format_endoint(None, "1.2.3.4", 8080)
    assert endpoint == "http://1.2.3.4:8080"

    endpoint = consul_sd.format_endoint("v42", "1.2.3.4", 8080)
    assert endpoint == "http://1.2.3.4:8080/v42"


async def test_consul_discovery_get_endpoint(consul_sd: AsyncConsulDiscovery):
    endpoint = await consul_sd.get_endpoint("dummy", "v1")
    assert endpoint == "http://8.8.8.8:1234/v1"


async def test_consul_discovery_resolve(consul_sd: AsyncConsulDiscovery):
    service = await consul_sd.resolve("dummy", "v1")
    assert service == Service(ServiceAddress="8.8.8.8", ServicePort=1234)


async def test_consul_discovery_resolve_unversionned_endpoint(
    consul_sd: AsyncConsulDiscovery,
):
    service = await consul_sd.resolve("dummy", None)
    assert service == Service(ServiceAddress="8.8.8.8", ServicePort=1234)


async def test_consul_discovery_resolve_unregistered(consul_sd: AsyncConsulDiscovery):
    with pytest.raises(UnregisteredServiceException) as ctx:
        await consul_sd.resolve("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"


async def test_consul_discovery_get_unversionned_endpoint(
    consul_sd: AsyncConsulDiscovery,
):
    endpoint = await consul_sd.get_endpoint("dummy", None)
    assert endpoint == "http://8.8.8.8:1234"


async def test_consul_discovery_get_endpoint_unregistered(
    consul_sd: AsyncConsulDiscovery,
):
    with pytest.raises(UnregisteredServiceException) as ctx:
        await consul_sd.get_endpoint("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"


async def test_consul_resolve_consul_error(consul_sd: AsyncConsulDiscovery):
    with pytest.raises(ConsulApiError) as ctx:
        await consul_sd.resolve("dummy", "v3")
    assert str(ctx.value) == "422 Unprocessable entity"


async def test_router_sd_get_endpoint_versionned(router_sd: AsyncRouterDiscovery):
    endpoint = await router_sd.get_endpoint("dummy", "v1")
    assert endpoint == "http://router/dummy-v1/v1"


async def test_router_sd_get_endpoint_unversionned(router_sd: AsyncRouterDiscovery):
    endpoint = await router_sd.get_endpoint("dummy", None)
    assert endpoint == "http://router/dummy"
