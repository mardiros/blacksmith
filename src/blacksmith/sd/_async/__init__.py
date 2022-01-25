from .adapters.consul import AsyncConsulDiscovery
from .adapters.router import AsyncRouterDiscovery
from .adapters.static import AsyncStaticDiscovery
from .base import AsyncAbstractServiceDiscovery

__all__ = [
    "AsyncAbstractServiceDiscovery",
    "AsyncConsulDiscovery",
    "AsyncRouterDiscovery",
    "AsyncStaticDiscovery",
]
