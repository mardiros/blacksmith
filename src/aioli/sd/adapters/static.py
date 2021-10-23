from __future__ import absolute_import, unicode_literals

from typing import Mapping, Tuple

from .. import UnregisteredServiceException
from ..base import AbtractServiceDiscovery, Url

Endpoint = Mapping[Tuple[str, str], Url]


class StaticDiscovery(AbtractServiceDiscovery):
    """
    A discovery instance based on a static dictionary.
    """
    endpoints: Endpoint

    def __init__(self, endpoints: Endpoint):
        self.endpoints = endpoints

    async def get_endpoint(self, service: str, version: str) -> Url:
        """
        Retrieve endpoint using the given parameters from `endpoints`.
        """
        try:
            return self.endpoints[(service, version)]
        except KeyError:
            raise UnregisteredServiceException(service, version)
