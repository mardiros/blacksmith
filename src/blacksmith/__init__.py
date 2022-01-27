import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("blacksmith").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass

from .domain.exceptions import HTTPError, HTTPTimeoutError
from .domain.model import (
    AbstractCachePolicy,
    AbstractCollectionParser,
    AbstractSerializer,
    AbstractTraceContext,
    CacheControlPolicy,
    CollectionIterator,
    CollectionParser,
    HeaderField,
    HTTPTimeout,
    JsonSerializer,
    PathInfoField,
    PostBodyField,
    PrometheusMetrics,
    QueryStringField,
    Request,
    Response,
    ResponseBox,
)
from .domain.model.http import HTTPRequest, HTTPResponse
from .domain.registry import register
from .domain.scanner import scan
from .middleware._async import (
    AsyncAbstractCache,
    AsyncCircuitBreakerMiddleware,
    AsyncHTTPAddHeadersMiddleware,
    AsyncHTTPAuthorizationMiddleware,
    AsyncHTTPBearerMiddleware,
    AsyncHTTPCacheMiddleware,
    AsyncHTTPMiddleware,
    AsyncMiddleware,
    AsyncPrometheusMiddleware,
    AsyncZipkinMiddleware,
)
from .middleware._sync import (
    SyncCircuitBreakerMiddleware,
    SyncHTTPAddHeadersMiddleware,
    SyncHTTPAuthorizationMiddleware,
    SyncHTTPBearerMiddleware,
    SyncHTTPCacheMiddleware,
    SyncHTTPMiddleware,
    SyncMiddleware,
    SyncPrometheusMiddleware,
)
from .sd._async import (
    AsyncAbstractServiceDiscovery,
    AsyncConsulDiscovery,
    AsyncRouterDiscovery,
    AsyncStaticDiscovery,
)
from .sd._sync import (
    SyncAbstractServiceDiscovery,
    SyncConsulDiscovery,
    SyncRouterDiscovery,
    SyncStaticDiscovery,
)
from .service._async.base import AsyncAbstractTransport
from .service._async.client import AsyncClient, AsyncClientFactory
from .service._sync.base import SyncAbstractTransport
from .service._sync.client import SyncClient, SyncClientFactory

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
    "CollectionParser",
    # Exceptions
    "HTTPError",
    "HTTPTimeoutError",
    # Timeout Config
    "HTTPTimeout",
    # Factories
    "AsyncClientFactory",
    "SyncClientFactory",
    "AsyncClient",
    "SyncClient",
    # Service Discovery
    "AsyncAbstractServiceDiscovery",
    "SyncAbstractServiceDiscovery",
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
    "AsyncHTTPAuthorizationMiddleware",
    "SyncHTTPAuthorizationMiddleware",
    "AsyncHTTPBearerMiddleware",
    "SyncHTTPBearerMiddleware",
    # Advanced Middlewares
    "AsyncCircuitBreakerMiddleware",
    "SyncCircuitBreakerMiddleware",
    "PrometheusMetrics",
    "AsyncPrometheusMiddleware",
    "SyncPrometheusMiddleware",
    "AbstractCachePolicy",
    "AbstractSerializer",
    "CacheControlPolicy",
    "JsonSerializer",
    "AsyncAbstractCache",
    "AsyncHTTPCacheMiddleware",
    "SyncHTTPCacheMiddleware",
    "AbstractTraceContext",
    "AsyncZipkinMiddleware",
    # Transport
    "AsyncAbstractTransport",
    "SyncAbstractTransport",
    "HTTPRequest",
    "HTTPResponse",
]
