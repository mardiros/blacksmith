from typing import Literal

from blacksmith import PathInfoField, Request, Response

from ..scanned_resources import registry


class GetParam(Request):
    name: str = PathInfoField(str)


class Bintje(Response):
    type: Literal["bintje"]
    name: str
    weight: float


class Amandine(Response):
    type: Literal["bintje"]
    name: str
    weight: float


registry.register(
    "vegetables",
    "potatoes",
    "vegetables",
    "v1",
    "/potatoes/{name}",
    {"GET": (GetParam, Bintje | Amandine)},
)
