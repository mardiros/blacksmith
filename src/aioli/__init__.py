import pkg_resources

__version__ = pkg_resources.get_distribution("aioli").version

from .domain.model import (
    AuthorizationHttpAuthentication,
    HeaderField,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Request,
    Response,
)
from .domain.registry import register
from .sd.adapters.static import StaticDiscovery
from .service.client import ClientFactory
