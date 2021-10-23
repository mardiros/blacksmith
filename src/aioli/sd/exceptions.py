from typing import Optional

from aioli.typing import ServiceName, Version


class UnregisteredServiceException(RuntimeError):
    """Raised when an unregistered service is beeing requested."""

    def __init__(self, service: ServiceName, version: Version) -> None:
        srv = f"{service}/{version}" if version else service
        super().__init__(f"Unregistered service {srv}")
