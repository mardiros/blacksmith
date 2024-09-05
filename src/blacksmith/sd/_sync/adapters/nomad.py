"""

The Nomad discovery strategy uses environment variables injected to discover
Consul Connect services, thus defined as upstreams to an application.
"""

import os

from blacksmith.domain.exceptions import UnregisteredServiceException
from blacksmith.typing import ServiceName, Version

from ..base import SyncAbstractServiceDiscovery, Url


class SyncNomadDiscovery(SyncAbstractServiceDiscovery):
    """
    A discovery instance based on Nomad environment variables.
    """

    def get_endpoint(self, service: ServiceName, version: Version = None) -> Url:
        """
        Retrieve endpoint using the given parameters from `endpoints`.
        """
        env_addr = os.getenv(f"NOMAD_UPSTREAM_ADDR_{service}")
        if not env_addr:
            raise UnregisteredServiceException(service, version)
        return f"http://{env_addr}"
