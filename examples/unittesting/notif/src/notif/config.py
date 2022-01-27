from typing import Any, Mapping

from fastapi import Depends
from notif.emailing import EmailSender

from blacksmith import AsyncClientFactory, AsyncConsulDiscovery


class AppConfig:
    def __init__(self, settings: Mapping[str, Any]):
        transport = settings.get("transport")
        sd = AsyncConsulDiscovery()
        self.get_client = AsyncClientFactory(sd=sd, transport=transport)
        self.send_email = settings.get("email_sender") or EmailSender(sd)

    async def initialize(self):
        await self.get_client.initialize()


class FastConfig:
    config: AppConfig
    depends = Depends(lambda: FastConfig.config)

    @classmethod
    async def configure(cls, settings: Mapping[str, Any]) -> None:
        cls.config = AppConfig(settings)
        await cls.config.initialize()
