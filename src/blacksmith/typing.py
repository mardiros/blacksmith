from typing import Optional, Tuple

from httpx import _types

Url = str
ServiceName = str
ClientName = str
ResourceName = str
Version = Optional[str]
Service = Tuple[str, Version]

Path = str
Proxies = _types.ProxiesTypes

try:
    from typing import Literal

    HttpLocation = Literal["path", "headers", "querystring", "body"]
    HttpMethod = Literal["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
except ImportError:
    HttpLocation = str
    HttpMethod = str
