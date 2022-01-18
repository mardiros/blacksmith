"""Trace with zipkin of jaegger."""

import abc
from typing import Any, Dict, Optional


class AbtractTraceContext(abc.ABC):
    """
    Interface of the trace context for the middleware.

    See examples with starlette-zipking for an implementation.
    """

    @classmethod
    @abc.abstractmethod
    def make_headers(cls) -> Dict[str, str]:
        """Build headers for the sub requests."""

    @abc.abstractmethod
    def __init__(self, name: str, kind: str = "SERVER") -> None:
        """Create a trace span for the current context."""

    @abc.abstractmethod
    def tag(self, key: str, value: str) -> "AbtractTraceContext":
        """Tag the span"""

    @abc.abstractmethod
    def annotate(
        self, value: Optional[str], ts: Optional[float] = None
    ) -> "AbtractTraceContext":
        """Annotate the span"""

    @abc.abstractmethod
    def __enter__(self) -> "AbtractTraceContext":
        """Make the created trace span of the current context the active span."""

    @abc.abstractmethod
    def __exit__(self, *exc: Any) -> None:
        """
        Ends the created trace span of the context, it parents become the active span.
        """
