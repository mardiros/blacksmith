"""Parsing Errors"""

from typing import Generic, TypeVar

from typing_extensions import Protocol

from .exceptions import HTTPError

TError_co = TypeVar("TError_co", covariant=True)


class AbstractErrorParser(Protocol, Generic[TError_co]):
    """
    A parser that parse the HTTPError class to become a pydantic model,
    represented by the generic ``TError_co`` here definabled in the
    SyncClientFactory and AsyncClientFactory.
    """

    def __call__(self, error: HTTPError) -> TError_co: ...


# The default error parser, does not parse the error,
# And, for legacy reason, the HTTPError cannot inherit from BaseModel
# Due to the HTTPError.json property which is incompatible to pydantic
# BaseModel.json() function.


def default_error_parser(error: HTTPError) -> HTTPError:
    return error
