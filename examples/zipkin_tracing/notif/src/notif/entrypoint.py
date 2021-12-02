from typing import cast

import aioli
import uvicorn
from asgiref.typing import ASGI3Application
from notif.views import app
from notif.zk_middleware import ZipkinMiddleware
from notif.aioli_middleware import AioliMiddleware


if __name__ == "__main__":
    aioli.scan("notif.resources")
    app.add_middleware(AioliMiddleware)
    app.add_middleware(ZipkinMiddleware, service_name="notif-v1")
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
