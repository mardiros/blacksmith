from typing import Any, Type

from blacksmith.typing import (
    ClientName,
    HTTPMethod,
    Json,
    Path,
    ResourceName,
    Service,
    ServiceName,
    Version,
)


class ConfigurationError(Exception):
    """Raised if there is a conflict for client and service."""

    def __init__(self, client: ClientName, service: Service, other: Service) -> None:
        super().__init__(
            f"Client {client} has been registered twice with "
            f"{service[0]}/{service[1]} and {other[0]}/{other[1]}"
        )


class UnregisteredServiceException(RuntimeError):
    """Raised when an unregistered service is beeing requested."""

    def __init__(self, service: ServiceName, version: Version) -> None:
        srv = f"{service}/{version}" if version else service
        super().__init__(f"Unregistered service '{srv}'")


class UnregisteredClientException(RuntimeError):
    """Raised when an unregistered service is beeing requested."""

    def __init__(self, client: ClientName) -> None:
        super().__init__(f"Unregistered client '{client}'")


class UnregisteredResourceException(RuntimeError):
    """Raised when an unregistered service is beeing requested."""

    def __init__(self, resource: ResourceName, client: ClientName) -> None:
        super().__init__(f"Unregistered resource '{resource}' in client '{client}'")


class UnregisteredRouteException(RuntimeError):
    """Raised when an unregistered service is beeing requested."""

    def __init__(
        self, route: HTTPMethod, resource: ResourceName, client: ClientName
    ) -> None:
        super().__init__(
            f"Unregistered route '{route}' in resource '{resource}' in "
            f"client '{client}'"
        )


class NoContractException(RuntimeError):
    """Raised when an unregistered service is beeing requested."""

    def __init__(
        self, method: HTTPMethod, resource: ResourceName, client: ClientName
    ) -> None:
        super().__init__(
            f"Unregistered route '{method}' in resource '{resource}' in "
            f"client '{client}'"
        )


class NoResponseSchemaException(RuntimeError):
    """Raised when an unregistered service is beeing requested."""

    def __init__(
        self, method: HTTPMethod, path: Path, resource: ResourceName, client: ClientName
    ) -> None:
        super().__init__(
            f"No response schema in route '{method} {path}' in resource'{resource}' "
            f"in client '{client}'"
        )


class WrongRequestTypeException(TypeError):
    def __init__(
        self,
        type: Type[Any],
        route: HTTPMethod,
        resource: ResourceName,
        client: ClientName,
    ) -> None:
        super().__init__(
            f"Invalid type '{type.__module__}.{type.__name__}' for route '{route}' "
            f"in resource '{resource}' in client '{client}'"
        )


class HTTPError(Exception):
    """Represent the http error."""

    from .model.http import HTTPRequest, HTTPResponse

    def __init__(self, message: str, request: HTTPRequest, response: HTTPResponse):
        super().__init__(message)
        self.request = request
        self.response = response

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def json(self) -> Json:
        return self.response.json

    @property
    def is_client_error(self) -> bool:
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        return 500 <= self.status_code < 600


class HTTPTimeoutError(TimeoutError):
    """Represent the http timeout error."""
