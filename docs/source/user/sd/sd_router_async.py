from blacksmith import AsyncRouterDiscovery

sd = AsyncRouterDiscovery(
    service_url_fmt="http://router/{service}/{version}",
    unversioned_service_url_fmt="http://router/{service}",
)
