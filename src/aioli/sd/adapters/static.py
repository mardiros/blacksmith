from __future__ import absolute_import, unicode_literals
from typing import Mapping

from ...typing import Service, ServiceName, Version
from .. import UnregisteredServiceException
from ..base import AbtractServiceDiscovery, Url

Endpoints = Mapping[Service, Url]


class StaticDiscovery(AbtractServiceDiscovery):
    """
    A discovery instance based on a static dictionary.
    """
    endpoints: Endpoints

    def __init__(self, endpoints: Endpoints) -> None:
        self.endpoints = endpoints

    async def get_endpoint(self, service: ServiceName, version: Version) -> Url:
        """
        Retrieve endpoint using the given parameters from `endpoints`.
        """
        try:
            return self.endpoints[(service, version)]
        except KeyError:
            raise UnregisteredServiceException(service, version)
