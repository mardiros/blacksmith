from functools import partial
from pydantic import BaseModel, Field
from ..typing import HttpLocation

PATH: HttpLocation = "PATH"
HEADER: HttpLocation = "HEADER"
QUERY: HttpLocation = "QUERY"
BODY: HttpLocation = "BODY"


PathInfoField = partial(Field, location=PATH)
"""Declare field that are serialized to the path info."""
HeaderField = partial(Field, location=HEADER)
"""Declare field that are serialized in http request header."""
QueryStringField = partial(Field, location=QUERY)
"""Declare field that are serialized in the http querystring."""
PostBodyField = partial(Field, location=BODY)
"""Declare field that are serialized in the json document."""


class Params(BaseModel):
    """HTTP Request Params Model."""


class Response(BaseModel):
    """HTTP Response Model."""
