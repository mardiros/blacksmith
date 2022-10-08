import asyncio
import datetime
import os
import sys
from typing import Any

from pydantic.fields import Field
from pydantic.main import BaseModel

from blacksmith import (
    AsyncClientFactory,
    AsyncHTTPAuthorizationMiddleware,
    AsyncStaticDiscovery,
    PathInfoField,
    QueryStringField,
    Request,
    Response,
    register,
)


class Dates(BaseModel):
    # We ignore fields we don't want to consume
    # created_at: datetime.datetime
    # registry_created_at: datetime.datetime
    registry_ends_at: datetime.datetime
    # updated_at: datetime.datetime


class PartialDomain(Response):
    # id: uuid.UUID
    # fqdn: str
    # In this example we rename a field in the response using `alias`
    name: str = Field(..., alias="fqdn_unicode")
    owner: str
    dates: Dates

class Contact(BaseModel):
    firstname: str = Field(alias="given")
    lastname: str = Field(alias="family")

class Contacts(BaseModel):
    owner: Contact = Field(...)

class Domain(Response):
    name: str = Field(alias="fqdn_unicode")
    contacts: Contacts
    dates: Dates


class DomainParam(Request):
    name: str = PathInfoField(...)


class CollectionDomainParam(Request):
    per_page: int = QueryStringField(2)


register(
    "gandi",
    "domain",
    "gandi",
    "v5",
    path="/domain/domains/{name}",
    contract={
        # In this example we don't provide the response model,
        # so we receive a dict for the json response
        "GET": (DomainParam, Domain),
    },
    collection_path="/domain/domains",
    collection_contract={
        "GET": (CollectionDomainParam, PartialDomain),
    },
)


async def main():
    if "GANDIV5_API_KEY" not in os.environ:
        print("Missing environment var GANDIV5_API_KEY", file=sys.stderr)
        sys.exit(-1)
    apikey = os.environ["GANDIV5_API_KEY"]
    sd = AsyncStaticDiscovery({("gandi", "v5"): "https://api.gandi.net/v5"})
    auth = AsyncHTTPAuthorizationMiddleware("Apikey", apikey)
    cli: AsyncClientFactory[PartialDomain, Any] = AsyncClientFactory(
        sd, timeout=(10.0)
    ).add_middleware(auth)
    api = await cli("gandi")
    if len(sys.argv) == 2:
        domain = sys.argv[1]
        domain_result = await api.domain.get(DomainParam(name=domain))
        domain = domain_result.unwrap()
        print(domain)
    else:
        domain_result = await api.domain.collection_get()
        domains = domain_result.unwrap()
        print(domains.meta)
        print()
        for domain in domains:
            print(domain)

asyncio.run(main())
