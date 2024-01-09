from enum import Enum
from typing import Any, Optional

import pytest
from result import Result

from blacksmith import (
    AsyncClientFactory,
    AsyncStaticDiscovery,
    CollectionIterator,
    HTTPError,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
    register,
)
from blacksmith.domain.exceptions import NoContractException
from blacksmith.domain.model.params import ResponseBox


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


class CreateItemIntSize(Request):
    name: str = PostBodyField()
    size: int = PostBodyField(2)


class ListItem(Request):
    name: Optional[str] = QueryStringField(None)


class GetItem(Request):
    item_name: str = PathInfoField()


class UpdateItem(GetItem):
    name: Optional[str] = PostBodyField(None)
    size: Optional[SizeEnum] = PostBodyField(None)


DeleteItem = GetItem


register(
    "api",
    "item",
    "api",
    None,
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


async def test_crud(dummy_api_endpoint: str):
    sd = AsyncStaticDiscovery({("api", None): dummy_api_endpoint})
    cli: AsyncClientFactory[HTTPError] = AsyncClientFactory(sd)
    api = await cli("api")

    items: Result[CollectionIterator[Any], HTTPError] = await api.item.collection_get()
    assert items.is_ok()
    llitems = list(items.unwrap())
    assert llitems == []

    resp = await api.item.collection_post(CreateItem(name="dummy0", size=SizeEnum.s))
    assert resp.is_ok()

    items = await api.item.collection_get(ListItem())
    litems = list(items.unwrap())
    assert litems == [Item(name="dummy0", size=SizeEnum.s)]

    resp = await api.item.collection_post({"name": "dummy1", "size": SizeEnum.m})
    assert resp.is_ok()

    items = await api.item.collection_get(ListItem())
    assert items.is_ok()
    litems = list(items.unwrap())
    assert litems == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy1", size=SizeEnum.m),
    ]

    # Test http error
    op_result = await api.item.collection_post(
        CreateItem(name="dummy0", size=SizeEnum.s)
    )
    assert op_result.is_err()
    exc = op_result.unwrap_err()
    assert exc.status_code == 409
    assert exc.json == {"detail": "Already Exists"}
    assert str(exc) == "api - POST /items - 409 Conflict"

    # Test the filter parameter in query string
    await api.item.collection_post({"name": "zdummy", "size": "L"})
    items = await api.item.collection_get(ListItem(name="z"))
    litems = list(items.unwrap())
    assert litems == [
        Item(name="zdummy", size=SizeEnum.l),
    ]

    # Test with the dict syntax
    items = await api.item.collection_get({"name": "z"})
    assert items.is_ok()
    litems = list(items.unwrap())
    assert litems == [
        Item(name="zdummy", size=SizeEnum.l),
    ]

    # Test get
    item: ResponseBox[Item, Any] = await api.item.get(GetItem(item_name="zdummy"))
    assert item.is_ok()
    assert item.unwrap() == Item(name="zdummy", size=SizeEnum.l)

    item = await api.item.get({"item_name": "zdummy"})
    assert item.is_ok()
    assert item.unwrap() == Item(name="zdummy", size=SizeEnum.l)

    item = await api.item.get({"item_name": "nonono"})
    assert item.is_err()
    exc = item.unwrap_err()
    assert exc.status_code == 404
    assert exc.json == {"detail": "Item not found"}

    # Test delete
    item = await api.item.delete({"item_name": "zdummy"})
    assert item.is_ok()
    items = await api.item.collection_get({})
    assert items.is_ok()
    litems = list(items.unwrap())
    assert litems == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy1", size=SizeEnum.m),
    ]

    # Test patch
    item = await api.item.patch({"item_name": "dummy1", "name": "dummy2"})
    assert item.is_ok()
    items = await api.item.collection_get()
    assert items.is_ok()
    litems = list(items.unwrap())
    assert litems == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy2", size=SizeEnum.m),
    ]

    op_result = await api.item.patch({"item_name": "dummy2", "size": "L"})
    assert op_result.is_ok()
    items = await api.item.collection_get()
    assert items.is_ok()
    litems = list(items.unwrap())
    assert litems == [
        Item(name="dummy0", size=SizeEnum.s),
        Item(name="dummy2", size=SizeEnum.l),
    ]

    with pytest.raises(NoContractException) as no_contract_exc:
        await api.item.put({})
    assert (
        str(no_contract_exc.value)
        == "Unregistered route 'PUT' in resource 'item' in client 'api'"
    )
