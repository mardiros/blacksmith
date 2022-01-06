from blacksmith import PathInfoField, Request, Response
from blacksmith.domain.model import PostBodyField
from blacksmith.domain.registry import Registry


class GetParam(Request):
    name: str = PathInfoField(str)


class PostParam(Request):
    name: str = PostBodyField(str)
    age: int = PostBodyField(int)


class GetResponse(Response):
    name: str
    age: int


dummy_registry = Registry()
dummy_registry.register(
    "api",
    "dummies",
    "dummy",
    "v1",
    "/dummies/{name}",
    {"GET": (GetParam, GetResponse)},
)
