from typing import Any, Literal, Optional, Tuple

from httpx import _types  # type: ignore

Url = str
ServiceName = str
ClientName = str
ResourceName = str
Version = Optional[str]
Service = Tuple[str, Version]

Path = str
Proxies = _types.ProxiesTypes

HttpLocation = Literal["path", "headers", "querystring", "body"]
HTTPMethod = Literal["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

Json = Optional[Any]
