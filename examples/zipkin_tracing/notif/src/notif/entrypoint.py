from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from notif.blacksmith_middleware import BlacksmithMiddleware
from notif.views import app
from notif.zk_middleware import ZipkinMiddleware

import blacksmith

if __name__ == "__main__":
    blacksmith.scan("notif.resources")
    app.add_middleware(BlacksmithMiddleware)
    app.add_middleware(ZipkinMiddleware, service_name="notif-v1")
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
