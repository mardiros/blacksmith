from blacksmith import PathInfoField, Request, Response

from .. import registry


class GetParam(Request):
    name: str = PathInfoField(str)


class GetResponse(Response):
    name: str
    weight: float


registry.register(
    "fruits",
    "cramberries",
    "fruits",
    "v1",
    "/cramberries/{name}",
    {"GET": (GetParam, GetResponse)},
)
