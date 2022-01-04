import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config


from notif.views import app, cli


async def main():
    config = Config()
    config.bind = ["0.0.0.0:8000"]
    await cli.initialize()
    await serve(app, config)


if __name__ == "__main__":
    asyncio.run(main())
