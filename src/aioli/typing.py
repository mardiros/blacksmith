from typing import Mapping, Optional, Tuple, Union

from pydantic import BaseModel

Url = str
ServiceName = str
ClientName = str
ResourceName = str
Version = Optional[str]
Service = Tuple[str, Version]

Path = str

try:
    from typing import Literal
    HttpLocation = Literal["path", "headers", "querystring", "body"]
    HttpMethod = Literal["HEAD", "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
except ImportError:
    HttpLocation = str
    HttpMethod = str
