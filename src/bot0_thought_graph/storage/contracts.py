"""Optional persistence contracts."""

from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    """Minimal optional key/value repository contract."""

    def load(self, key: str) -> T:
        """Load a value by key."""

    def save(self, key: str, value: T) -> None:
        """Save a value by key."""


class ThoughtRepository(Repository[Any], Protocol):
    """Semantic alias for repositories storing thought-graph values."""
