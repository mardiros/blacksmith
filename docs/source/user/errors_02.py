from result import Result

from blacksmith import (
    CollectionIterator,
    ResponseBox,
    SyncClientFactory,
    SyncStaticDiscovery,
)

from .resources import Item, PartialItem


def main():
    sd = SyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = SyncClientFactory(sd)
    api = cli("api")
    items: Result[CollectionIterator[PartialItem]] = api.item.collection_get()
    if items.is_ok():
        for item in items.unwrap():
            rfull_item: ResponseBox[Item] = api.item.get({"name": item.name})
            if rfull_item.is_err():
                print(f"Unexpected error: {rfull_item.json}")
                continue
            full_item = rfull_item.unwrap()
            print(full_item)
    err = items.unwrap_err()
    print(f"Unexpected error: {err.json}")
