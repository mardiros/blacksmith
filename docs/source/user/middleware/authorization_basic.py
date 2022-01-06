import base64
from blacksmith import AsyncClientFactory, AsyncConsulDiscovery, AsyncHTTPAuthorization


class AsyncBasicAuthorization(AsyncHTTPAuthorization):
    def __init__(self, username, password):
        userpass = f"{username}:{password}".encode("utf-8")
        b64head = base64.b64encode(userpass).decode("ascii")
        header = f"Basic {b64head}"
        return super().__init__("Basic", header)


sd = AsyncConsulDiscovery()
auth = AsyncBasicAuthorization("alice", "secret")
cli = AsyncClientFactory(sd).add_middleware(auth)
