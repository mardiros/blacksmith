from blacksmith import CollectionIterator, SyncClientFactory, SyncStaticDiscovery

from .resources import Item, PartialItem


def main():
    sd = SyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = SyncClientFactory(sd)
    api = cli("api")
    items: CollectionIterator[PartialItem] = api.item.collection_get()
    for item in items:
        full_item: Item = (api.item.get({"name": item.name})).response
        print(full_item)
