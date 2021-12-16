import json
from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from notif.views import app
from starlette_zipkin import B3Headers, ZipkinConfig, ZipkinMiddleware

import blacksmith

if __name__ == "__main__":
    blacksmith.scan("notif.resources")
    config = ZipkinConfig(
        host="zipkin",
        port=9411,
        service_name="notif-v1",
        sample_rate=1.0,
        inject_response_headers=True,
        force_new_trace=False,
        json_encoder=json.dumps,
        header_formatter=B3Headers,
    )
    app.add_middleware(ZipkinMiddleware, config=config)
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
