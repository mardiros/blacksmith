from blacksmith import AsyncConsulDiscovery

# all parameters here are optional, the value
# here are the defaults one for the example.
sd = AsyncConsulDiscovery(
    "http://consul:8500/v1",
    service_name_fmt="{service}-{version}",
    service_url_fmt="http://{address}:{port}/{version}",
    unversioned_service_name_fmt="{service}",
    unversioned_service_url_fmt="http://{address}:{port}",
    consul_token="abc",
)
