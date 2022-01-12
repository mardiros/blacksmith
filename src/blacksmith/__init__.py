import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("blacksmith").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass

from .domain.exceptions import HTTPError, HTTPTimeoutError
from .domain.model import (
    AbstractCollectionParser,
    AbtractTraceContext,
    CollectionIterator,
    HeaderField,
    HTTPTimeout,
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
    AsyncHTTPCachingMiddleware,
    AsyncHTTPMiddleware,
    AsyncMiddleware,
    AsyncPrometheusMetrics,
    AsyncZipkinMiddleware,
)
from .middleware._sync import (
    SyncCircuitBreaker,
    SyncHTTPAddHeadersMiddleware,
    SyncHTTPAuthorization,
    SyncHTTPBearerAuthorization,
    SyncHTTPCachingMiddleware,
    SyncHTTPMiddleware,
    SyncMiddleware,
    SyncPrometheusMetrics,
)
from .sd._async.adapters.consul import AsyncConsulDiscovery
from .sd._async.adapters.router import AsyncRouterDiscovery
from .sd._async.adapters.static import AsyncStaticDiscovery
from .sd._sync.adapters.consul import SyncConsulDiscovery
from .sd._sync.adapters.router import SyncRouterDiscovery
from .sd._sync.adapters.static import SyncStaticDiscovery
from .service._async.client import AsyncClientFactory
from .service._sync.client import SyncClientFactory

__all__ = [
    # Ordered for the doc
    # Request / Response
    "scan",
    "register",
    "Request",
    "Response",
    "HeaderField",
    "PathInfoField",
    "PostBodyField",
    "QueryStringField",
    # Request / Response Boxing
    "ResponseBox",
    "CollectionIterator",
    "AbstractCollectionParser",
    # Exceptions
    "HTTPError",
    "HTTPTimeoutError",
    # Timeout Config
    "HTTPTimeout",
    # Factories
    "AsyncClientFactory",
    "SyncClientFactory",
    # Service Discovery
    "AsyncConsulDiscovery",
    "SyncConsulDiscovery",
    "AsyncRouterDiscovery",
    "SyncRouterDiscovery",
    "AsyncStaticDiscovery",
    "SyncStaticDiscovery",
    # Middlewares
    "AsyncMiddleware",
    "SyncMiddleware",
    # Basic Middlewares
    "AsyncHTTPMiddleware",
    "SyncHTTPMiddleware",
    "AsyncHTTPAddHeadersMiddleware",
    "SyncHTTPAddHeadersMiddleware",
    "AsyncHTTPAuthorization",
    "SyncHTTPAuthorization",
    "AsyncHTTPBearerAuthorization",
    "SyncHTTPBearerAuthorization",
    # Advanced Middlewares
    "AsyncCircuitBreaker",
    "SyncCircuitBreaker",
    "AsyncPrometheusMetrics",
    "SyncPrometheusMetrics",
    "AsyncHTTPCachingMiddleware",
    "SyncHTTPCachingMiddleware",
    "AbtractTraceContext",
    "AsyncZipkinMiddleware",
]
