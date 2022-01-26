from typing import Mapping, TypeVar, Union

from fastapi import Depends, FastAPI

from blacksmith import AsyncClientFactory, AsyncConsulDiscovery, AsyncRouterDiscovery



class AppConfig:
    def __init__(self, settings: Mapping):
        self.settings = settings
        transport = self.settings.get("transport")
        sd = AsyncRouterDiscovery(
            self.settings["service_url_fmt"],
            self.settings["unversioned_service_url_fmt"],
        )
        self.get_client = AsyncClientFactory(sd=sd, transport=transport)

    async def initialize(self):
        await self.get_client.initialize()

    # async def get_smtp_endpoint(self):
    #     srv = await self.smtp_sd.resolve("smtp", None)
    #     return srv


class FastConfig:
    config: AppConfig
    depends = Depends(lambda: FastConfig.config)

    @classmethod
    async def configure(cls, settings: Mapping) -> None:
        cls.config = AppConfig(settings)
        await cls.config.initialize()
