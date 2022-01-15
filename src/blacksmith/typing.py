from typing import Optional, Tuple

from httpx import _types
from typing_extensions import Literal

Url = str
ServiceName = str
ClientName = str
ResourceName = str
Version = Optional[str]
Service = Tuple[str, Version]

Path = str
Proxies = _types.ProxiesTypes

HttpLocation = Literal["path", "headers", "querystring", "body"]
HttpMethod = Literal["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
