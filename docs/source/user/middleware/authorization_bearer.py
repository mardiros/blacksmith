from blacksmith import (
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncHTTPBearerAuthorization,
)

access_token = "abc"

sd = AsyncConsulDiscovery()
auth = AsyncHTTPBearerAuthorization(access_token)
cli = AsyncClientFactory(sd).add_middleware(auth)
# Now every call of the client will have the header
# Authorization: Bearer abc


async def main():
    api = await cli("api")
    protected_resource = await api.protected_resource.get({})  # noqa
