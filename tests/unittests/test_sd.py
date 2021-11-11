import pytest

from aioli.sd.adapters.static import StaticDiscovery
from aioli.sd.adapters.consul import ConsulDiscovery
from aioli.domain.exceptions import UnregisteredServiceException


@pytest.mark.asyncio
async def test_static_discovery(static_sd):
    endpoint = await static_sd.get_endpoint("dummy", "v1")
    assert endpoint == "https://dummy.v1/"


@pytest.mark.asyncio
async def test_static_discovery_raise(static_sd: StaticDiscovery):
    with pytest.raises(UnregisteredServiceException) as ctx:
        await static_sd.get_endpoint("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"


@pytest.mark.asyncio
async def test_consul_discovery_get_service_name(consul_sd: ConsulDiscovery):
    name = consul_sd.format_service_name("dummy-name", None)
    assert name == "dummy-name"

    name = consul_sd.format_service_name("dummy-name", "v42")
    assert name == "dummy-name-v42"

@pytest.mark.asyncio
async def test_consul_discovery_format_endoint(consul_sd: ConsulDiscovery):
    endpoint = consul_sd.format_endoint(None, "1.2.3.4", 8080)
    assert endpoint == "http://1.2.3.4:8080"

    endpoint = consul_sd.format_endoint("v42", "1.2.3.4", 8080)
    assert endpoint == "http://1.2.3.4:8080/v42"


@pytest.mark.asyncio
async def test_consul_discovery_get_endpoint(consul_sd: ConsulDiscovery):
    endpoint = await consul_sd.get_endpoint("dummy", "v1")
    assert endpoint == "http://8.8.8.8:1234/v1"

@pytest.mark.asyncio
async def test_consul_discovery_get_unversionned_endpoint(consul_sd: ConsulDiscovery):
    endpoint = await consul_sd.get_endpoint("dummy", None)
    assert endpoint == "http://8.8.8.8:1234"

@pytest.mark.asyncio
async def test_consul_discovery_get_endpoint_unregistered(consul_sd: ConsulDiscovery):
    with pytest.raises(UnregisteredServiceException) as ctx:
        await consul_sd.get_endpoint("dummy", "v2")
    assert str(ctx.value) == "Unregistered service 'dummy/v2'"
