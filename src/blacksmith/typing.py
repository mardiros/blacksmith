from typing import Any, Literal, Optional

Url = str
ServiceName = str
ClientName = str
ResourceName = str
Version = Optional[str]
Service = tuple[str, Version]

Path = str
Proxies = dict[str, str]

HttpLocation = Literal["path", "headers", "querystring", "body"]
HTTPMethod = Literal["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

Json = Optional[Any]
