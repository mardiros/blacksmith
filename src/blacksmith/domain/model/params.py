import abc
from dataclasses import dataclass
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pydantic.typing import IntStr
else:
    IntStr = str

from ...domain.exceptions import NoResponseSchemaException
from ...typing import (
    ClientName,
    HttpLocation,
    HTTPMethod,
    Json,
    Path,
    ResourceName,
    Url,
)
from .http import HTTPRequest, HTTPResponse, Links

PATH: HttpLocation = "path"
HEADER: HttpLocation = "headers"
QUERY: HttpLocation = "querystring"
BODY: HttpLocation = "body"


PathInfoField = partial(Field, location=PATH)
"""Declare field that are serialized to the path info."""
HeaderField = partial(Field, location=HEADER)
"""Declare field that are serialized in http request header."""
QueryStringField = partial(Field, location=QUERY)
"""Declare field that are serialized in the http querystring."""
PostBodyField = partial(Field, location=BODY)
"""Declare field that are serialized in the json document."""


class Request(BaseModel):
    """
    Request Params Model.

    Fields must use subclass :func:`.PathInfoField`, :func:`.HeaderField`,
    :func:`.QueryStringField` or :func:`.PostBodyField` to declare each fields.
    """

    def to_http_request(self, method: HTTPMethod, url_pattern: Url) -> HTTPRequest:
        """Convert the request params to an http request in order to serialize
        the http request for the client.
        """
        req = HTTPRequest(method, url_pattern)
        fields_by_loc: Dict[HttpLocation, Dict[IntStr, Any]] = {
            HEADER: {},
            PATH: {},
            QUERY: {},
            BODY: {},
        }
        for field in self.__fields__.values():
            loc = cast(
                HttpLocation,
                field.field_info.extra["location"],  # type: ignore
            )
            fields_by_loc[loc].update({field.name: ...})

        headers = self.dict(
            include=fields_by_loc[HEADER], by_alias=True, exclude_none=True
        )
        req.headers = {key: str(val) for key, val in headers.items()}
        req.path = self.dict(
            include=fields_by_loc[PATH], by_alias=True, exclude_none=False
        )
        req.querystring = self.dict(
            include=fields_by_loc[QUERY], by_alias=True, exclude_none=True
        )
        req.body = self.json(
            include=fields_by_loc[BODY], by_alias=True, exclude_none=False
        )
        return req


TResponse = TypeVar("TResponse", bound="Response")
TCollectionResponse = TypeVar("TCollectionResponse", bound="Response")


class Response(BaseModel):
    """Response Model."""

    @classmethod
    def from_http_response(
        cls: Type[TResponse], response: HTTPResponse
    ) -> Optional[TResponse]:
        """Build the response from the given HTTPResponse."""
        return cls(**response.json) if response.json else None


@dataclass
class Metadata:
    """Metadata of a collection response."""

    count: int
    total_count: Optional[int]
    links: Links


class AbstractCollectionParser(abc.ABC):
    """
    Signature of the collection parser.
    """

    resp: HTTPResponse

    def __init__(self, resp: HTTPResponse):
        self.resp = resp

    @property
    @abc.abstractmethod
    def meta(self) -> Metadata:
        """
        Return the metatadata from the response.

        Usually, metadata are in a header, but if the API wrap the list,

        ::

            {
                "total_items": 0,
                "items": []
            }


        Then, the ``Metadata.total_count`` can be extracted from the json,
        instead of the header.
        """

    @property
    @abc.abstractmethod
    def json(self) -> List[Any]:
        """
        Return the list part of the response the response.

        For instance, if an API wrap the list in a structure like

        ::

            {
                "items": [
                    {"objkey": "objval"}
                ]
            }

        then, the ``resp.json["items"]`` has to be returned.
        """


class CollectionParser(AbstractCollectionParser):
    """
    Handle the rest collection metadata parser.

    Deserialize how a collection is wrapped.
    """

    total_count_header: str = "Total-Count"

    @property
    def meta(self) -> Metadata:
        total_count = self.resp.headers.get(self.total_count_header)
        return Metadata(
            count=len(self.json),
            total_count=None if total_count is None else int(total_count),
            links=self.resp.links,
        )

    @property
    def json(self) -> List[Json]:
        return self.resp.json or []


class ResponseBox(Generic[TResponse]):
    """
    Wrap an http response to deseriaze it.

    It's also allow users to write some userfull typing inference such as:

    ::

        user: User = (await api.user.get({"username": username})).response
        print(user.username)  # declaring the type User make code analyzer happy.
    """

    def __init__(
        self,
        response: HTTPResponse,
        response_schema: Optional[Type[Response]],
        method: HTTPMethod,
        path: Path,
        name: ResourceName,
        client_name: ClientName,
    ) -> None:
        self.http_response = response
        self.response_schema = response_schema
        self.method: HTTPMethod = method
        self.path: Path = path
        self.name: ResourceName = name
        self.client_name: ClientName = client_name

    @property
    def json(self) -> Optional[Dict[str, Any]]:
        """Return the raw json response."""
        return self.http_response.json

    @property
    def response(self) -> TResponse:
        """
        Parse the response using the schema.

        :raises NoResponseSchemaException: if the response_schema has not been
            set in the contract.
        """
        if self.response_schema is None:
            raise NoResponseSchemaException(
                self.method, self.path, self.name, self.client_name
            )
        resp = self.response_schema(**(self.json or {}))
        return cast(TResponse, resp)


class CollectionIterator(Iterator[TResponse]):
    """
    Deserialize the models in a json response list, item by item.
    """

    response: AbstractCollectionParser

    def __init__(
        self,
        response: HTTPResponse,
        response_schema: Optional[Type[Response]],
        collection_parser: Type[AbstractCollectionParser],
    ) -> None:
        self.pos = 0
        self.response_schema = response_schema
        self.response = collection_parser(response)
        self.json_resp = self.response.json

    @property
    def meta(self) -> Metadata:
        """
        Get the response metadata such as counts in http header, links...

        Those metadata are generated by the collection_parser.
        """
        return self.response.meta

    def __next__(self) -> TResponse:
        try:
            resp = self.json_resp[self.pos]
            if self.response_schema:
                resp = self.response_schema(**resp)
        except IndexError:
            raise StopIteration()

        self.pos += 1
        return cast(TResponse, resp)  # Could be a dict

    def __iter__(self) -> "CollectionIterator[TResponse]":
        return self
