from blacksmith import PathInfoField, Request, Response

from .. import registry


class GetParam(Request):
    name: str = PathInfoField(str)


class GetResponse(Response):
    name: str
    weight: float


registry.register(
    "vegetables",
    "potatoes",
    "vegetables",
    "v1",
    "/potatoes/{name}",
    {"GET": (GetParam, GetResponse)},
)
