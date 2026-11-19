from blacksmith import (
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
    register,
)


class Item(Response):
    name: str = ""


class CreateItem(Request):
    name: str = PostBodyField()


class CreateItemIntSize(Request):
    name: str = PostBodyField()


class ListItem(Request):
    name: str | None = QueryStringField(None)


class GetItem(Request):
    item_name: str = PathInfoField()


class UpdateItem(GetItem):
    name: str | None = PostBodyField(None)


DeleteItem = GetItem


register(
    client_name="extra",
    resource="dummies",
    service="extra",
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
