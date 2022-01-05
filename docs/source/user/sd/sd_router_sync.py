from blacksmith import SyncRouterDiscovery

sd = SyncRouterDiscovery(
    service_url_fmt="http://router/{service}/{version}",
    unversioned_service_url_fmt="http://router/{service}",
)
