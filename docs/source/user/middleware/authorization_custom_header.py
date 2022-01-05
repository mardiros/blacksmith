from blacksmith import (
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncHTTPAddHeadersMiddleware,
)


class AsyncBasicAuthorization(AsyncHTTPAddHeadersMiddleware):
    def __init__(self, secret):
        return super().__init__(headers={"X-Secret": secret})


sd = AsyncConsulDiscovery()
auth = AsyncBasicAuthorization("secret")
cli = AsyncClientFactory(sd).add_middleware(auth)
