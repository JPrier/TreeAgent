"""Minimal stub of the litellm API used for tests."""

from typing import Any, Callable


def with_structured_output(schema: Any) -> Callable[[Any], Any]:
    """Return a decorator that validates structured output.

    This is a lightweight placeholder and simply returns a function that
    returns the provided value without calling any model.
    """

    def decorator(fn: Callable[[Any], Any]) -> Callable[[Any], Any]:
        def wrapper(value: Any) -> Any:
            return value

        return wrapper

    return decorator
