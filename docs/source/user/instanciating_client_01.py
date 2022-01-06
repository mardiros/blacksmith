from blacksmith import AsyncClientFactory, AsyncStaticDiscovery


async def main():
    sd = AsyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = AsyncClientFactory(sd)
    api = await cli("api")
    items = await api.item.collection_get()
    print(items)
