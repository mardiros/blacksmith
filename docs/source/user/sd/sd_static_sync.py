from blacksmith import SyncStaticDiscovery

sd = SyncStaticDiscovery(
    {
        ("gandi", "v5"): "https://api.gandi.net/v5/",
        ("github", None): "https://api.github.com/",
        ("sendinblue", "v3"): "https://api.sendinblue.com/v3/",
    }
)
