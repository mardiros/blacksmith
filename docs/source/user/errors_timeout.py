from blacksmith import HTTPTimeout, AsyncClientFactory, AsyncStaticDiscovery

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
    resources = await api.resource.collection_get()  # noqa

    # force the timeout
    resources = await api.resource.collection_get(timeout=42.0)  # noqa

    # Or even with a connect timeout using the HTTPTimeout class
    resources = await api.resource.collection_get(  # noqa
        timeout=HTTPTimeout(42.0, 7.0)
    )
