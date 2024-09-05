from blacksmith import SyncNomadDiscovery

# no parameter needed, discovery use environment variables.
sd = SyncNomadDiscovery()

# no version needed, only the service name
service = sd.get_endpoint("service_name")
