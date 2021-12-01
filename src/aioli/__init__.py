import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("aioli-client").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass

from .domain.model import (
    HeaderField,
    HTTPAuthorization,
    HTTPUnauthenticated,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
)
from .domain.registry import register
from .domain.scanner import scan
from .monitoring import AbstractMetricsCollector
from .monitoring.adapters import PrometheusMetrics
from .sd.adapters.consul import ConsulDiscovery
from .sd.adapters.router import RouterDiscovery
from .sd.adapters.static import StaticDiscovery
from .service.client import ClientFactory, CollectionIterator
