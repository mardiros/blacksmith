import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

import blacksmith
from notif.config import FastConfig
from notif.views import fastapi

DEFAULT_SETTINGS = {
    "service_url_fmt": "http://router/{service}-{version}/{version}",
    "unversioned_service_url_fmt": "http://router/{service}",
}


async def main(settings=None):
    blacksmith.scan("notif.resources")
    config = Config()
    config.bind = ["0.0.0.0:8000"]
    config.reload = True
    await FastConfig.configure(DEFAULT_SETTINGS)
    await serve(fastapi, config)


if __name__ == "__main__":
    asyncio.run(main())
