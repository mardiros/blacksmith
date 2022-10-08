from result import Result

from blacksmith import (
    AsyncClientFactory,
    AsyncStaticDiscovery,
    CollectionIterator,
    ResponseBox,
)

from .resources import Item, PartialItem


async def main():
    sd = AsyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = AsyncClientFactory(sd)
    api = await cli("api")
    items: Result[CollectionIterator[PartialItem]] = await api.item.collection_get()
    if items.is_ok():
        for item in items.unwrap():
            rfull_item: ResponseBox[Item] = await api.item.get({"name": item.name})
            if rfull_item.is_err():
                print(f"Unexpected error: {rfull_item.json}")
                continue
            full_item = rfull_item.unwrap()
            print(full_item)
    err = items.unwrap_err()
    print(f"Unexpected error: {err.json}")
