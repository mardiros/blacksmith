from blacksmith import AsyncClientFactory, AsyncStaticDiscovery, CollectionIterator

from .resources import Item, PartialItem


async def main():
    sd = AsyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = AsyncClientFactory(sd)
    api = await cli("api")
    items: CollectionIterator[PartialItem] = await api.item.collection_get()
    for item in items:
        full_item: Item = (await api.item.get({"name": item.name})).response
        print(full_item)
