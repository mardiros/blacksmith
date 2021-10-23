import pytest

from aioli.sd import UnregisteredServiceException
from aioli.sd.adapters import StaticDiscovery


@pytest.mark.asyncio
async def test_static_discovery(static_sd):
    endpoint = await static_sd.get_endpoint("dummy", "v1")
    assert endpoint == "https://dummy.v1/"


@pytest.mark.asyncio
async def test_static_discovery_raise(static_sd):
    with pytest.raises(UnregisteredServiceException) as ctx:
        await static_sd.get_endpoint("dummy", "v2")
    assert str(ctx.value) == "Unregistered service dummy/v2"
