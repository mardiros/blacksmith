import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("aioli-client").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass

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
