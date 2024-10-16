from blacksmith import AsyncClientFactory, AsyncStaticDiscovery, HTTPTimeout

sd = AsyncStaticDiscovery({})

# read timeout at 5 seconds
# and connect timeout at 5 seconds
cli = AsyncClientFactory(sd, timeout=(10.0, 5.0))
# Or
cli = AsyncClientFactory(sd, timeout=HTTPTimeout(10.0, 5.0))

# All timeout at 10 seconds
cli = AsyncClientFactory(sd, timeout=10.0)
# Or
cli = AsyncClientFactory(sd, timeout=HTTPTimeout(10.0))


async def main():
    api = await cli("api")

    # user the default timeout
    resp = await api.resource.collection_get()

    # force the timeout
    resp = await api.resource.collection_get(timeout=42.0)

    # Or even with a connect timeout using the HTTPTimeout class
    resp = await api.resource.collection_get(timeout=HTTPTimeout(42.0, 7.0))  # noqa
