from importlib import metadata

__version__ = metadata.version("blacksmith")

from .domain.error import AbstractErrorParser, TError_co, default_error_parser
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
    TCollectionResponse,
    TResponse,
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
    AsyncNomadDiscovery,
    AsyncRouterDiscovery,
    AsyncStaticDiscovery,
)
from .sd._sync import (
    SyncAbstractServiceDiscovery,
    SyncConsulDiscovery,
    SyncNomadDiscovery,
    SyncRouterDiscovery,
    SyncStaticDiscovery,
)
from .service._async.base import AsyncAbstractTransport
from .service._async.client import AsyncClient, AsyncClientFactory
from .service._async.route_proxy import AsyncRouteProxy
from .service._sync.base import SyncAbstractTransport
from .service._sync.client import SyncClient, SyncClientFactory
from .service._sync.route_proxy import SyncRouteProxy
from .service.http_body_serializer import (
    AbstractHttpBodySerializer,
    register_http_body_serializer,
    unregister_http_body_serializer,
)

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
    "TResponse",
    "TCollectionResponse",
    # Exceptions
    "HTTPError",
    "HTTPTimeoutError",
    # Errors,
    "AbstractErrorParser",
    "TError_co",
    "default_error_parser",
    # Timeout Config
    "HTTPTimeout",
    # Client
    "AsyncClientFactory",
    "SyncClientFactory",
    "AsyncClient",
    "SyncClient",
    "AsyncRouteProxy",
    "SyncRouteProxy",
    # Service Discovery
    "AsyncAbstractServiceDiscovery",
    "SyncAbstractServiceDiscovery",
    "AsyncConsulDiscovery",
    "SyncConsulDiscovery",
    "AsyncNomadDiscovery",
    "SyncNomadDiscovery",
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
    # Serializer,
    "AbstractHttpBodySerializer",
    "register_http_body_serializer",
    "unregister_http_body_serializer",
]
