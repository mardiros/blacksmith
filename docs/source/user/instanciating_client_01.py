from blacksmith import AsyncClientFactory, AsyncStaticDiscovery


async def main():
    sd = AsyncStaticDiscovery({("api", None): "http://srv:8000/"})
    cli = AsyncClientFactory(sd)
    api = await cli("api")
    result = await api.item.collection_get()
    if result.is_ok():
        for item in result.unwrap():
            print(item)
    else:
        print(result.unwrap_err())
