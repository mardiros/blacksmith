import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("blacksmith").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass

from .domain.model import (
    CollectionIterator,
    HeaderField,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
    ResponseBox,
)
from .domain.registry import register
from .domain.scanner import scan
from .middleware import (
    CircuitBreaker,
    HTTPAddHeadersMiddleware,
    HTTPAuthorization,
    HTTPBearerAuthorization,
    HTTPMiddleware,
    Middleware,
    PrometheusMetrics,
)
from .sd.adapters.consul import ConsulDiscovery
from .sd.adapters.router import RouterDiscovery
from .sd.adapters.static import StaticDiscovery
from .service.client import ClientFactory
