"""Retry handler with exponential backoff using tenacity."""

import logging
from typing import Callable, Any, Optional, Type
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)


logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 60,
    exception_types: Optional[tuple] = None,
) -> Callable:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exception_types: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """
    if exception_types is None:
        exception_types = (Exception,)

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exception_types),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


class RetryHandler:
    """Handler for retry operations with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: int = 1,
        max_wait: int = 60,
    ):
        """Initialize retry handler.

        Args:
            max_attempts: Maximum number of retry attempts
            min_wait: Minimum wait time in seconds
            max_wait: Maximum wait time in seconds
        """
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait

    def execute(
        self,
        func: Callable,
        *args,
        exception_types: Optional[tuple] = None,
        **kwargs,
    ) -> Any:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            exception_types: Exception types to retry on
            **kwargs: Keyword arguments for func

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        if exception_types is None:
            exception_types = (Exception,)

        decorated_func = with_retry(
            max_attempts=self.max_attempts,
            min_wait=self.min_wait,
            max_wait=self.max_wait,
            exception_types=exception_types,
        )(func)

        return decorated_func(*args, **kwargs)
