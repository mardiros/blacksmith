from typing import Any, Literal, overload

import pytest

from blacksmith import (
    AsyncClientFactory,
    AsyncClientProtocol,
    AsyncStaticDiscovery,
    Attachment,
    HTTPError,
    ResponseBox,
    scan,
)
from blacksmith.domain.exceptions import NoContractException
from tests.functionals.resources.api.items import (
    CreateItem,
    GetItem,
    Item,
    ListItem,
    SizeEnum,
)
from tests.functionals.resources.api.upload import (
    UploadComplexRequest,
    UploadedFile,
    UploadQuery,
    UploadRequest,
)
from tests.functionals.resources.typing import APIClient, ExtraClient


class AppClientFactory(AsyncClientFactory[HTTPError, Literal["api", "extra"]]):
    @overload
    async def __call__(self, client_name: Literal["api"]) -> APIClient: ...

    @overload
    async def __call__(self, client_name: Literal["extra"]) -> ExtraClient: ...

    async def __call__(
        self, client_name: Literal["api", "extra"]
    ) -> AsyncClientProtocol[HTTPError]:
        return await super().__call__(client_name)


@pytest.fixture(autouse=True, scope="module")
def blacksmith_scan():
    scan("tests.functionals.resources")


async def test_crud(dummy_api_endpoint: str):
    sd = AsyncStaticDiscovery({("api", None): dummy_api_endpoint})
    cli = AppClientFactory(sd)
    api = await cli("api")

    items = await api.item.collection_get()
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


async def test_attachment(dummy_api_endpoint: str):
    sd = AsyncStaticDiscovery({("api", None): dummy_api_endpoint})
    cli = AppClientFactory(sd)
    api = await cli("api")
    resp = await api.upload.post(
        UploadRequest(
            foobar="FooBar", attachmt=Attachment(filename="bar.xml", content=b"<ok/>")
        )
    )
    assert resp.is_ok()
    assert resp.unwrap() == UploadedFile(
        foobar="FooBar", filename="bar.xml", content="<ok/>"
    )


async def test_attachment_json(dummy_api_endpoint: str):
    sd = AsyncStaticDiscovery({("api", None): dummy_api_endpoint})
    cli = AppClientFactory(sd)
    api = await cli("api")
    resp = await api.upload_complex.post(
        UploadComplexRequest(
            foobar=UploadQuery(name="foo", value=42),
            attachmt=Attachment(filename="bar.xml", content=b"<ok/>"),
        )
    )
    assert resp.is_ok()
    assert resp.unwrap() == UploadedFile(
        foobar='{"name": "foo", "value": 42}', filename="bar.xml", content="<ok/>"
    )
