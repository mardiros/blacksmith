from typing import Any, Mapping

from fastapi import Depends

from blacksmith import AsyncClientFactory, AsyncRouterDiscovery


class AppConfig:
    def __init__(self, settings: Mapping[str, Any]):
        transport = settings.get("transport")
        sd = AsyncRouterDiscovery(
            settings["service_url_fmt"],
            settings["unversioned_service_url_fmt"],
        )
        self.get_client = AsyncClientFactory(sd=sd, transport=transport)


class FastConfig:
    config: AppConfig
    depends = Depends(lambda: FastConfig.config)

    @classmethod
    def configure(cls, settings: Mapping[str, Any]) -> None:
        cls.config = AppConfig(settings)
