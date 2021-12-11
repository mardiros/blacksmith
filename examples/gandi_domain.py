import asyncio
import datetime
import os
import sys
from typing import Iterable, cast

from pydantic.fields import Field
from pydantic.main import BaseModel

import aioli
from aioli import (
    ClientFactory,
    CollectionIterator,
    HTTPAuthorization,
    PathInfoField,
    QueryStringField,
    Request,
    Response,
    StaticDiscovery,
)


class Dates(BaseModel):
    # We ignore fields we don't want to consume
    # created_at: datetime.datetime
    # registry_created_at: datetime.datetime
    registry_ends_at: datetime.datetime
    # updated_at: datetime.datetime


class ListDomainResponse(Response):
    # id: uuid.UUID
    # fqdn: str
    # In this example we rename a field in the response using `alias`
    name: str = Field(str, alias="fqdn_unicode")
    owner: str
    dates: Dates


class DomainParam(Request):
    name: str = PathInfoField(str)


class CollectionDomainParam(Request):
    per_page: int = QueryStringField(2)


aioli.register(
    "gandi",
    "domain",
    "gandi",
    "v5",
    path="/domain/domains/{name}",
    contract={
        # In this example we don't provide the response model,
        # so we receive a dict for the json response
        "GET": (DomainParam, None),
    },
    collection_path="/domain/domains",
    collection_contract={
        "GET": (CollectionDomainParam, ListDomainResponse),
    },
)


async def main():
    if "GANDIV5_API_KEY" not in os.environ:
        print("Missing environment var GANDIV5_API_KEY", file=sys.stderr)
        sys.exit(-1)
    apikey = os.environ["GANDIV5_API_KEY"]
    sd = StaticDiscovery({("gandi", "v5"): "https://api.gandi.net/v5"})
    auth = HTTPAuthorization("Apikey", apikey)
    cli = ClientFactory(sd, auth, timeout=(10.0))
    api = await cli("gandi")
    if len(sys.argv) == 2:
        domain = sys.argv[1]
        domain = await api.domain.get(DomainParam(name=domain))
        print(domain.json)
    else:
        domains: CollectionIterator[
            ListDomainResponse
        ] = await api.domain.collection_get(auth=auth)

        print(domains.meta)
        print()
        for domain in domains:
            print(domain)
            print(domain.name)


asyncio.run(main())
