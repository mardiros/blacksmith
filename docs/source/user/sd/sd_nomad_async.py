from blacksmith import AsyncNomadDiscovery

# no parameter needed, discovery use environment variables.
sd = AsyncNomadDiscovery()

# no version needed, only the service name
service = sd.get_endpoint("service_name")
