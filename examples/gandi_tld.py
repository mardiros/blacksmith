import asyncio
import os
import sys
from typing import Any

from pydantic import BaseModel

from blacksmith import (
    AsyncClientFactory,
    AsyncHTTPAuthorizationMiddleware,
    AsyncStaticDiscovery,
    HTTPError,
    PathInfoField,
    Request,
    Response,
    register,
)


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


class APIError(BaseModel):
    message: str
    object: str
    cause: str
    code: int


def error_parser(err: HTTPError) -> APIError:
    return APIError(**err.json)


register(
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
    sd = AsyncStaticDiscovery({("gandi", "v5"): "https://api.gandi.net/v5"})
    auth = AsyncHTTPAuthorizationMiddleware("Apikey", apikey)
    cli: AsyncClientFactory[Any, TLDResponse, APIError] = AsyncClientFactory(
        sd, error_parser=error_parser
    ).add_middleware(auth)
    api = await cli("gandi")

    tld = (await api.tld.get(TLDInfoGetParam(name="eu"))).unwrap()
    print(tld)

    tld = (await api.tld.get(TLDInfoGetParam(name="europ"))).unwrap_err()
    print(tld)


asyncio.run(main())
