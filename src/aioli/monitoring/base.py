"""Define base class for the monitoring"""
import abc

from aioli.typing import ClientName, HttpMethod, ServiceName, Version


class AbstractMetricsCollector(abc.ABC):
    """Define the monitoring metrics interface."""

    @abc.abstractmethod
    def inc_request(
        self,
        client_name: ClientName,
        method: HttpMethod,
        path: str,
        status_code: int,
    ):
        """Increment the number of request made."""


class SinkholeMetrics(AbstractMetricsCollector):
    """A metrics collector that does not collect them."""

    def inc_request(
        self,
        client_name: ClientName,
        method: HttpMethod,
        path: str,
        status_code: int,
    ):
        pass
