from enum import Enum
from typing import Optional

import pytest
from pydantic import BaseModel

import aioli
from aioli import Params, Response
from aioli.domain.model import PathInfoField, PostBodyField, QueryStringField
from aioli.sd.adapters.static import StaticDiscovery
from aioli.service.client import ClientFactory


class SizeEnum(str, Enum):
    s = "S"
    m = "M"
    l = "L"


class Item(Response):
    name: str = ""
    size: SizeEnum = SizeEnum.m


class PatchItem(BaseModel):
    name: Optional[str] = None
    size: Optional[SizeEnum] = None


class CreateItem(Params):
    name: str = PostBodyField()
    size: SizeEnum = PostBodyField(SizeEnum.m)


class ListItem(Params):
    name: Optional[str] = QueryStringField(None)


class GetItem(Params):
    item_name: str = PathInfoField()


class PatchItem(GetItem):
    name: Optional[str] = PostBodyField(None)
    size: Optional[SizeEnum] = PostBodyField(None)


DeleteItem = GetItem


aioli.register(
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
        "PATCH": (PatchItem, None),
        "DELETE": (DeleteItem, None),
    },
)


@pytest.mark.asyncio
async def test_crud(dummy_api_endpoint):
    sd = StaticDiscovery({("api", None): dummy_api_endpoint})
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

    await api.item.collection_post({"name": "zdummy", "size": "L"})

    # Test the filter parameter in query string
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
    item = await api.item.get(GetItem(item_name="zdummy"))
    assert item == Item(name="zdummy", size=SizeEnum.l)

    item = await api.item.get({"item_name": "zdummy"})
    assert item == Item(name="zdummy", size=SizeEnum.l)

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
