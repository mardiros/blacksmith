from result import Result

from blacksmith import AsyncClientFactory, AsyncStaticDiscovery, CollectionIterator

from .resources import Item, PartialItem


async def main():
    sd = AsyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = AsyncClientFactory(sd)
    api = await cli("api")
    items: Result[CollectionIterator[PartialItem]] = await api.item.collection_get()
    for item in items.unwrap():
        full_item: Item = (await api.item.get({"name": item.name})).unwrap()
        print(full_item)
