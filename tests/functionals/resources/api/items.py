from enum import StrEnum

from blacksmith import (
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
    register,
)


class SizeEnum(StrEnum):
    s = "S"
    m = "M"
    l = "L"


class Item(Response):
    name: str = ""
    size: SizeEnum = SizeEnum.m


class CreateItem(Request):
    name: str = PostBodyField()
    size: SizeEnum = PostBodyField(SizeEnum.m)


class CreateItemIntSize(Request):
    name: str = PostBodyField()
    size: int = PostBodyField(2)


class ListItem(Request):
    name: str | None = QueryStringField(None)


class GetItem(Request):
    item_name: str = PathInfoField()


class UpdateItem(GetItem):
    name: str | None = PostBodyField(None)
    size: SizeEnum | None = PostBodyField(None)


DeleteItem = GetItem


register(
    client_name="api",
    resource="item",
    service="api",
    version=None,
    collection_path="/items",
    collection_contract={
        "GET": (ListItem, Item),
        "POST": (CreateItem | CreateItemIntSize, None),
    },
    path="/items/{item_name}",
    contract={
        "GET": (GetItem, Item),
        "PATCH": (UpdateItem, None),
        "DELETE": (DeleteItem, None),
    },
)
