from enum import Enum
from typing import Optional

import pytest

import blacksmith
from blacksmith import (
    ClientFactory,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
    AsyncStaticDiscovery,
)
from blacksmith.domain.exceptions import HTTPError, NoContractException


class SizeEnum(str, Enum):
    s = "S"
    m = "M"
    l = "L"


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
        "GET": (ListItem, Item),
        "POST": (CreateItem, None),
    },
    path="/items/{item_name}",
    contract={
        "GET": (GetItem, Item),
        "PATCH": (UpdateItem, None),
        "DELETE": (DeleteItem, None),
    },
)


@pytest.mark.asyncio
async def test_crud(dummy_api_endpoint):
    sd = AsyncStaticDiscovery({("api", None): dummy_api_endpoint})
    cli = ClientFactory(sd)
    api = await cli("api")

    items = await api.item.collection_get()
    items = list(items)
    assert items == []

    await api.item.collection_post(CreateItem(name="dummy0", size=SizeEnum.s))

    items = await api.item.collection_get(ListItem())
    items = list(items)
    assert items == [Item(name="dummy0", size=SizeEnum.s)]

    await api.item.collection_post({"name": "dummy1", "size": SizeEnum.m})

    items = await api.item.collection_get(ListItem())
    items = list(items)
    assert items == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy1", size=SizeEnum.m),
    ]

    # Test http error
    with pytest.raises(HTTPError) as exc:
        await api.item.collection_post(CreateItem(name="dummy0", size=SizeEnum.s))
    assert exc.value.status_code == 409
    assert exc.value.json == {"detail": "Already Exists"}
    assert str(exc.value) == "409 Conflict"

    # Test the filter parameter in query string
    await api.item.collection_post({"name": "zdummy", "size": "L"})
    items = await api.item.collection_get(ListItem(name="z"))
    items = list(items)
    assert items == [
        Item(name="zdummy", size=SizeEnum.l),
    ]

    # Test with the dict syntax
    items = await api.item.collection_get({"name": "z"})
    items = list(items)
    assert items == [
        Item(name="zdummy", size=SizeEnum.l),
    ]

    # Test get
    item: Item = (await api.item.get(GetItem(item_name="zdummy"))).response
    assert item == Item(name="zdummy", size=SizeEnum.l)

    item = (await api.item.get({"item_name": "zdummy"})).response
    assert item == Item(name="zdummy", size=SizeEnum.l)

    with pytest.raises(HTTPError) as exc:
        item = (await api.item.get({"item_name": "nonono"})).response
    assert exc.value.status_code == 404
    assert exc.value.json == {"detail": "Item not found"}

    # Test delete
    await api.item.delete({"item_name": "zdummy"})
    items = await api.item.collection_get({})
    items = list(items)
    assert items == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy1", size=SizeEnum.m),
    ]

    # Test patch
    await api.item.patch({"item_name": "dummy1", "name": "dummy2"})
    items = await api.item.collection_get()
    items = list(items)
    assert items == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy2", size=SizeEnum.m),
    ]

    await api.item.patch({"item_name": "dummy2", "size": "L"})
    items = await api.item.collection_get()
    items = list(items)
    assert items == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy2", size=SizeEnum.l),
    ]

    with pytest.raises(NoContractException) as exc:
        items = await api.item.put({})
    assert (
        str(exc.value) == "Unregistered route 'PUT' in resource 'item' in client 'api'"
    )
