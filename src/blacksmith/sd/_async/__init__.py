from .adapters.consul import AsyncConsulDiscovery
from .adapters.nomad import AsyncNomadDiscovery
from .adapters.router import AsyncRouterDiscovery
from .adapters.static import AsyncStaticDiscovery
from .base import AsyncAbstractServiceDiscovery

__all__ = [
    "AsyncAbstractServiceDiscovery",
    "AsyncConsulDiscovery",
    "AsyncNomadDiscovery",
    "AsyncRouterDiscovery",
    "AsyncStaticDiscovery",
]
