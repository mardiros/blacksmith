import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("blacksmith").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass

from .domain.exceptions import HTTPError, TimeoutError
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
from .middleware._async import (
    AsyncCircuitBreaker,
    AsyncHTTPAddHeadersMiddleware,
    AsyncHTTPAuthorization,
    AsyncHTTPBearerAuthorization,
    AsyncHttpCachingMiddleware,
    AsyncHTTPMiddleware,
    AsyncMiddleware,
    AsyncPrometheusMetrics,
)
from .sd._async.adapters.consul import AsyncConsulDiscovery
from .sd._async.adapters.router import AsyncRouterDiscovery
from .sd._async.adapters.static import AsyncStaticDiscovery
from .service._async.client import AsyncClientFactory

__all__ = [
    "AsyncCircuitBreaker",
    "AsyncClientFactory",
    "AsyncConsulDiscovery",
    "AsyncHTTPAddHeadersMiddleware",
    "AsyncHTTPAuthorization",
    "AsyncHTTPBearerAuthorization",
    "AsyncHttpCachingMiddleware",
    "AsyncHTTPMiddleware",
    "AsyncMiddleware",
    "AsyncPrometheusMetrics",
    "AsyncRouterDiscovery",
    "AsyncStaticDiscovery",
    "CollectionIterator",
    "HeaderField",
    "HTTPError",
    "PathInfoField",
    "PostBodyField",
    "QueryStringField",
    "register",
    "Request",
    "Response",
    "ResponseBox",
    "scan",
    "TimeoutError",
]
