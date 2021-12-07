"""Define base class for the monitoring"""
import abc

from aioli.typing import ClientName, HttpMethod, ServiceName, Version


class AbstractMetricsCollector(abc.ABC):
    """Define the monitoring metrics interface."""

    @abc.abstractmethod
    def observe_request(
        self,
        client_name: ClientName,
        method: HttpMethod,
        path: str,
        status_code: int,
        latency: float,
    ):
        """Collect observed request in a metrics registry."""


class SinkholeMetrics(AbstractMetricsCollector):
    """A metrics collector that does not collect them."""

    def observe_request(
        self,
        client_name: ClientName,
        method: HttpMethod,
        path: str,
        status_code: int,
        latency: float,
    ):
        """Ignore the observed value."""
