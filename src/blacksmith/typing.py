from typing import Any, Literal

Url = str
ServiceName = str
ClientName = str
ResourceName = str
Version = str | None
Service = tuple[str, Version]

Path = str
Proxies = dict[str, str]

HttpLocation = Literal["path", "header", "query", "body", "attachment"]
HTTPMethod = Literal["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

Json = Any
