from enum import Enum
from typing import Optional

import blacksmith
from blacksmith import PathInfoField, PostBodyField, QueryStringField, Request, Response


class SizeEnum(str, Enum):
    s = "S"
    m = "M"
    l = "L"


class PartialItem(Response):
    name: str = ""


class Item(Response):
    name: str = ""
    size: SizeEnum = SizeEnum.m


class CreateItem(Request):
    name: str = PostBodyField()
    size: SizeEnum = PostBodyField(SizeEnum.m)


class ListItem(Request):
    name: Optional[str] = QueryStringField(None)


class GetItem(Request):
    item_name: str = PathInfoField()


class UpdateItem(GetItem):
    name: Optional[str] = PostBodyField(None)
    size: Optional[SizeEnum] = PostBodyField(None)


DeleteItem = GetItem

blacksmith.register(
    "api",
    "item",
    "api",
    None,
    collection_path="/items",
    collection_contract={
        "GET": (ListItem, PartialItem),
        "POST": (CreateItem, None),
    },
    path="/items/{item_name}",
    contract={
        "GET": (GetItem, Item),
        "PATCH": (UpdateItem, None),
        "DELETE": (DeleteItem, None),
    },
)
