from enum import Enum
from multiprocessing import Process
from typing import Dict, List, Optional, cast
from asgiref.typing import ASGI3Application

import pytest
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic.fields import Field
from starlette.responses import Response

from aioli.sd.adapters import StaticDiscovery
from aioli.sd.adapters.static import Endpoints

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


items_db: Dict[str, Item] = {}
not_found = HTTPException(404, "Item not found")


@app.get("/items", response_model=List[Item])
def list_items(name: Optional[str] = None):
    if name:
        return [item for item in items_db.values() if item.name.startswith(name)]
    return sorted(items_db.values(), key= lambda item: item.name)


@app.post("/items")
def create_item(item: Item):
    if item.name in items_db:
        raise HTTPException(409, "Already Exists")
    items_db[item.name] = item
    return {"href": app.url_path_for("read_item", item_name=item.name)}


@app.get("/items/{item_name}")
def read_item(item_name: str, response_model=Item):
    try:
        return items_db[item_name]
    except KeyError:
        raise not_found


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
    except KeyError:
        raise not_found


@app.delete("/items/{item_name}")
def delete_item(item_name: str, item: PatchItem):
    try:
        del items_db[item_name]
        return Response("", 204)
    except KeyError:
        raise not_found


def run_server(port):
    uvicorn.run(cast(ASGI3Application, app), port=port)


@pytest.fixture
def dummy_api_endpoint():
    port = 6556
    proc = Process(target=run_server, args=(port,), daemon=True)
    proc.start()
    yield f"http://localhost:{port}"
    proc.kill()  # Cleanup after test


if __name__ == "__main__":
    run_server(6556)
