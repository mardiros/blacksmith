
from pydantic import BaseModel, Field
from result import Result

from blacksmith import (
    AsyncClientFactory,
    AsyncStaticDiscovery,
    CollectionIterator,
    ResponseBox,
)
from blacksmith.domain.exceptions import HTTPError
from blacksmith.domain.model.http import HTTPRequest

from .resources import Item, PartialItem


class APIError(BaseModel):
    request: HTTPRequest = Field(...)
    message: str = Field(...)
    detail: str | None = Field(None)


def error_parser(error: HTTPError) -> APIError:
    return APIError(request=error.request, **error.json)


async def main():
    sd = AsyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = AsyncClientFactory(sd, error_parser=error_parser)
    api = await cli("api")
    items: Result[CollectionIterator[PartialItem], APIError] = (
        await api.item.collection_get()
    )
    if items.is_ok():
        for item in items.unwrap():
            rfull_item: ResponseBox[Item, APIError] = await api.item.get(
                {"name": item.name}
            )
            if rfull_item.is_err():
                print(f"Unexpected error: {rfull_item.json}")
                continue
            full_item = rfull_item.unwrap()
            print(full_item)
    else:
        # In this case, the error is not an APIError instance
        # build using the error_parser.
        err = items.unwrap_err()
        print(f"Unexpected error: {err}")
