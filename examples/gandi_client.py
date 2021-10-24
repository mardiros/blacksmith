import aioli
from aioli import Params, PathInfoField
from aioli.domain.model import Response
from aioli.service.client import ClientFactory


class TLDInfoGetParam(Params):
    name: str = PathInfoField(str)


class TLDReturn(Response):
    name: str
    category: str
    lock: str
    ext_trade: bool
    authinfo_for_transfer: bool
    change_owner: bool
    corporate: bool
    # Unused parameters
    # 'full_tld': 'eu',
    # 'href': 'https://api.gandi.net/v5/domain/tlds/eu'


aioli.register(
    "gandi",
    "tld",
    "gandi",
    "v5",
    path="/domain/tlds/{name}",
    contract={
        "GET": (TLDInfoGetParam, TLDReturn),
    },
)

import asyncio
from aioli.sd.adapters import StaticDiscovery
from aioli.service.adapters.httpx import HttpxTransport



async def main():
    sd = StaticDiscovery(
        {
            ("gandi", "v5"): "https://api.gandi.net/v5/"
        }
    )
    tp = HttpxTransport()
    cli = ClientFactory(sd, tp)
    api = await cli("gandi")
    tld = await api.tld.get(TLDInfoGetParam(name="eu"))
    print(tld)


asyncio.run(main())
