from typing import Mapping

from fastapi import Depends
from notif.emailing import EmailSender

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
        self.transport = self.settings.get("transport")

        self.send_email = settings.get("email_sender") or EmailSender(
            AsyncConsulDiscovery()
        )

    async def initialize(self):
        await self.get_client.initialize()


class FastConfig:
    config: AppConfig
    depends = Depends(lambda: FastConfig.config)

    @classmethod
    async def configure(cls, settings: Mapping) -> None:
        cls.config = AppConfig(settings)
        await cls.config.initialize()
