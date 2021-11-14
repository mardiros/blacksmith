import pkg_resources

__version__ = pkg_resources.get_distribution("aioli").version

from .domain.model import (
    HTTPUnauthenticated,
    HTTPAuthorization,
    HeaderField,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
)
from .domain.registry import register
from .domain.scanner import scan
from .sd.adapters.static import StaticDiscovery
from .sd.adapters.consul import ConsulDiscovery
from .sd.adapters.router import RouterDiscovery
from .service.client import ClientFactory
