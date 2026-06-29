"""

The Nomad discovery strategy uses environment variables injected to discover
Consul Connect services, thus defined as upstreams to an application.
"""

import os

from blacksmith.domain.exceptions import UnregisteredServiceException
from blacksmith.typing import ServiceName, Version

from ..base import AsyncAbstractServiceDiscovery, Url


class AsyncNomadDiscovery(AsyncAbstractServiceDiscovery):
    """
    A discovery instance based on Nomad environment variables.
    """

    def __init__(
        self,
        service_url_fmt: str = "http://{nomad_upstream_addr}/{version}",
        service_env_fmt: str = "NOMAD_UPSTREAM_ADDR_{service}_{version}",
        unversioned_service_url_fmt: str = "http://{nomad_upstream_addr}",
        unversioned_service_env_fmt: str = "NOMAD_UPSTREAM_ADDR_{service}",
    ) -> None:
        """ """
        self.service_url_fmt = service_url_fmt
        self.service_env_fmt = service_env_fmt
        self.unversioned_service_url_fmt = unversioned_service_url_fmt
        self.unversioned_service_env_fmt = unversioned_service_env_fmt
        # External services discovery
        self.service_real_addr_fmt: str = "UPSTREAM_REAL_ADDR_{service_key}"
        self.service_real_scheme_fmt: str = "UPSTREAM_REAL_SCHEME_{service_key}"

    async def get_endpoint(self, service: ServiceName, version: Version = None) -> Url:
        """
        Retrieve endpoint using the given parameters from `endpoints`.
        """
        lookup_key = f"{service}_{version}" if version else service
        real_upstream_addr = os.getenv(
            self.service_real_addr_fmt.format(service_key=lookup_key)
        )
        if real_upstream_addr:
            lookup_scheme = self.service_real_scheme_fmt.format(service_key=lookup_key)
            real_upstream_scheme = os.getenv(lookup_scheme, "http")
            end_url = f"/{version}" if version else ""
            return f"{real_upstream_scheme}://{real_upstream_addr}{end_url}"

        # Nomad normal environment variables mechanism
        env_fmt = self.service_env_fmt if version else self.unversioned_service_env_fmt
        nomad_upstream_addr = os.getenv(
            env_fmt.format(service=service, version=version)
        )
        if not nomad_upstream_addr:
            raise UnregisteredServiceException(service, version)
        url_fmt = self.service_url_fmt if version else self.unversioned_service_url_fmt
        return url_fmt.format(nomad_upstream_addr=nomad_upstream_addr, version=version)
