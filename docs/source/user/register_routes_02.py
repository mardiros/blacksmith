import blacksmith


class SearchItem(blacksmith.Request):
    name_like = blacksmith.QueryStringField(alias="~name")


class Item(blacksmith.Response):
    name: str


blacksmith.register(
    client_name="api",
    resource="item",
    service="datastore",
    version="v1",
    path="/search",
    collection_contract={
        "GET": (SearchItem, Item),
    },
)
