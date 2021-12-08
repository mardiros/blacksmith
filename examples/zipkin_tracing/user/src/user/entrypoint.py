from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from user.views import app
from user.zk_middleware import ZipkinMiddleware

if __name__ == "__main__":
    app.add_middleware(
        ZipkinMiddleware,
        service_name="user-v1",
        endpoint="http://zipkin:9411/",
    )
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
