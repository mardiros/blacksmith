import asyncio
import signal
import socket
from collections.abc import AsyncIterator
from enum import StrEnum
from typing import Annotated, Any, cast

import pytest
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from hypercorn.typing import ASGIFramework
from pydantic import BaseModel
from pydantic.fields import Field
from starlette.responses import Response


async def wait_for_socket(
    host: str, port: int, timeout: int = 5, poll_time: float = 0.05
):
    """Wait until the socket is open before proceeding."""
    for _ in range(timeout * int(1 / poll_time)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                break
        await asyncio.sleep(poll_time)
    else:
        raise RuntimeError(f"Server on {host}:{port} did not start in time.")


async def wait_for_socket_free(
    host: str, port: int, timeout: int = 5, poll_time: float = 0.05
):
    """Wait until the socket is open before proceeding."""
    for _ in range(timeout * int(1 / poll_time)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                await asyncio.sleep(poll_time)
            else:
                break
    else:
        raise RuntimeError(f"Server on {host}:{port} did not start in time.")


app = FastAPI()


class SizeEnum(StrEnum):
    s = "S"
    m = "M"
    l = "L"


class Item(BaseModel):
    name: str = Field("")
    size: SizeEnum = Field(SizeEnum.m)


class PatchItem(BaseModel):
    name: str | None = None
    size: SizeEnum | None = None


items_db: dict[str, Item] = {}
not_found = HTTPException(404, "Item not found")


@app.get("/items", response_model=list[Item])
async def list_items(name: str | None = None):
    if name:
        return [item for item in items_db.values() if item.name.startswith(name)]
    return sorted(items_db.values(), key=lambda item: item.name)


@app.post("/items")
async def create_item(item: Item):
    if item.name in items_db:
        raise HTTPException(409, "Already Exists")
    items_db[item.name] = item
    return {"href": app.url_path_for("read_item", item_name=item.name)}


@app.get("/items/{item_name}")
async def read_item(item_name: str, response_model: type[BaseModel] = Item):
    try:
        return items_db[item_name]
    except KeyError as exc:
        raise not_found from exc


@app.patch("/items/{item_name}")
async def update_item(item_name: str, item: PatchItem):
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
async def delete_item(item_name: str):
    try:
        del items_db[item_name]
        return Response("", 204)
    except KeyError as exc:
        raise not_found from exc


@app.post("/upload")
async def upload(
    request: Request,
    foobar: Annotated[str, Form()],
    attachmt: Annotated[UploadFile, File()],
):
    content = await attachmt.read()
    return {
        "foobar": foobar,
        "filename": attachmt.filename,
        "content": content,
    }


@app.post("/upload-complex")
async def upload_complex(
    request: Request,
    foobar: Annotated[str, Form()],
    attachmt: Annotated[UploadFile, File()],
):
    content = await attachmt.read()
    return {
        "foobar": foobar,
        "filename": attachmt.filename,
        "content": content,
    }


@pytest.fixture(scope="session")
async def dummy_api_endpoint() -> AsyncIterator[str]:
    host, port = "127.0.0.1", 6556

    shutdown_event = asyncio.Event()

    def _signal_handler(*_: Any) -> None:
        shutdown_event.set()

    config = HypercornConfig()
    config.bind = [f"{host}:{port}"]
    config.worker_class = "asyncio"
    config.loglevel = "error"

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)

    server_task = asyncio.create_task(
        serve(
            cast(ASGIFramework, app),
            config,
            shutdown_trigger=shutdown_event.wait,
        )
    )
    await wait_for_socket(host, port)
    yield f"http://{host}:{port}"

    server_task.cancel()  # Cleanup after test
    await wait_for_socket_free(host, port)
