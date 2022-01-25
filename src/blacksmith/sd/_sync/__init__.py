from .adapters.consul import SyncConsulDiscovery
from .adapters.router import SyncRouterDiscovery
from .adapters.static import SyncStaticDiscovery
from .base import SyncAbstractServiceDiscovery

__all__ = [
    "SyncAbstractServiceDiscovery",
    "SyncConsulDiscovery",
    "SyncRouterDiscovery",
    "SyncStaticDiscovery",
]
