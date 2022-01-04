import asyncio
import os
import sys

import blacksmith
from blacksmith import HTTPAuthorization, PathInfoField, Request, Response
from blacksmith.sd._async.adapters import StaticDiscovery
from blacksmith.service.client import ClientFactory


class TLDInfoGetParam(Request):
    name: str = PathInfoField(str)


class TLDResponse(Response):
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


blacksmith.register(
    "gandi",
    "tld",
    "gandi",
    "v5",
    path="/domain/tlds/{name}",
    contract={
        "GET": (TLDInfoGetParam, TLDResponse),
    },
)


async def main():
    if "GANDIV5_API_KEY" not in os.environ:
        print("Missing environment var GANDIV5_API_KEY", file=sys.stderr)
        sys.exit(-1)
    apikey = os.environ["GANDIV5_API_KEY"]
    sd = StaticDiscovery({("gandi", "v5"): "https://api.gandi.net/v5"})
    auth = HTTPAuthorization("Apikey", apikey)
    cli = ClientFactory(sd).add_middleware(auth)
    api = await cli("gandi")
    tld: TLDResponse = (await api.tld.get(TLDInfoGetParam(name="eu"))).response
    print(tld)


asyncio.run(main())
