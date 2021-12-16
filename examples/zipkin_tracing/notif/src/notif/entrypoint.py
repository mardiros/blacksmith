from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from notif.views import app
from starlette_zipkin import ZipkinConfig, ZipkinMiddleware

import blacksmith

if __name__ == "__main__":
    blacksmith.scan("notif.resources")
    config = ZipkinConfig(
        host="zipkin",
        port=9411,
        service_name="notif-v1",
    )
    app.add_middleware(ZipkinMiddleware, config=config)
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
