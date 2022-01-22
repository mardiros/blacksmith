from blacksmith import (
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncHTTPBearerMiddleware,
)

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd)


async def a_dummy_api_view(request):
    api = await cli("api")
    api.add_middleware(AsyncHTTPBearerMiddleware(request.access_token))
    protected_resource = await api.protected_resource.get({})  # noqa
