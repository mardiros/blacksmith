from collections.abc import Iterable
from enum import Enum
from multiprocessing import Process
from typing import Optional

import httpx
import pytest
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic.fields import Field
from starlette.responses import Response

app = FastAPI()


class SizeEnum(str, Enum):
    s = "S"
    m = "M"
    l = "L"


class Item(BaseModel):
    name: str = Field("")
    size: SizeEnum = Field(SizeEnum.m)


class PatchItem(BaseModel):
    name: Optional[str] = None
    size: Optional[SizeEnum] = None


items_db: dict[str, Item] = {}
not_found = HTTPException(404, "Item not found")


@app.get("/items", response_model=list[Item])
def list_items(name: Optional[str] = None):
    if name:
        return [item for item in items_db.values() if item.name.startswith(name)]
    return sorted(items_db.values(), key=lambda item: item.name)


@app.post("/items")
def create_item(item: Item):
    if item.name in items_db:
        raise HTTPException(409, "Already Exists")
    items_db[item.name] = item
    return {"href": app.url_path_for("read_item", item_name=item.name)}


@app.get("/items/{item_name}")
def read_item(item_name: str, response_model: type[BaseModel] = Item):
    try:
        return items_db[item_name]
    except KeyError as exc:
        raise not_found from exc


@app.patch("/items/{item_name}")
def update_item(item_name: str, item: PatchItem):
    try:
        cur = items_db.pop(item_name)
        if item.name is not None:
            cur.name = item.name
        if item.size is not None:
            cur.size = item.size
        items_db[cur.name] = cur
        return {"href": app.url_path_for("read_item", item_name=cur.name)}
    except KeyError as exc:
        raise not_found from exc


@app.delete("/items/{item_name}")
def delete_item(item_name: str):
    try:
        del items_db[item_name]
        return Response("", 204)
    except KeyError as exc:
        raise not_found from exc


def run_server(port: int):
    uvicorn.run(app, port=port)


@pytest.fixture(scope="session")
def dummy_api_endpoint() -> Iterable[str]:
    port = 6556
    proc = Process(target=run_server, args=(port,), daemon=True)
    proc.start()
    for i in range(20):
        timeout = 0.1 / (i + 1)
        try:
            httpx.get(f"http://localhost:{port}", timeout=httpx.Timeout(timeout))
        except httpx.ConnectError:
            pass
        else:
            break
    yield f"http://localhost:{port}"
    proc.kill()  # Cleanup after test


if __name__ == "__main__":
    run_server(6556)
