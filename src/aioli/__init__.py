import pkg_resources

__version__ = pkg_resources.get_distribution("aioli").version

from .domain.model import (
    AuthorizationHttpAuthentication,
    HeaderField,
    Request,
    PathInfoField,
    PostBodyField,
    QueryStringField,
    Response,
)
from .domain.registry import register
from .service.client import ClientFactory
