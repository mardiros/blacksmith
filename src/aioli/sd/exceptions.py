from typing import Optional


class UnregisteredServiceException(Exception):
    """Raised when an unregistered service is beeing requested."""

    def __init__(self, service: str, version: Optional[str]):
        srv = f"{service}/{version}" if version else service
        super().__init__(f"Unregistered service {srv}")
