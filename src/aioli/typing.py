from typing import Literal, Mapping, Optional, Tuple, Union

from pydantic import BaseModel

Url = str
ServiceName = str
ClientName = str
ResourceName = str
Version = Optional[str]
Service = Tuple[str, Version]

Path = str
HttpLocation = Literal["PATH", "HEADER", "QUERY", "BODY"]
HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
