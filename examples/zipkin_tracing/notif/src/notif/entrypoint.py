import uvicorn
from notif.views import app
from starlette_zipkin import ZipkinConfig, ZipkinMiddleware

import blacksmith

if __name__ == "__main__":
    blacksmith.scan("notif.resources")
    config = ZipkinConfig(
        host="jaeger",
        port=9411,
        service_name="notif-v1",
    )
    app.add_middleware(ZipkinMiddleware, config=config)
    uvicorn.run(app, host="0.0.0.0", port=8000)
