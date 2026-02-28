"""Circuit breaker pattern implementation using pybreaker."""

import logging
from typing import Callable, Any, Optional
from pybreaker import CircuitBreaker as PyCircuitBreaker
from pybreaker import CircuitBreakerError


logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures.

    Wraps pybreaker with a simplified interface.
    """

    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        reset_timeout: int = 60,
    ):
        """Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            fail_max: Maximum failures before opening circuit
            reset_timeout: Seconds before attempting to close circuit
        """
        self.name = name
        self.breaker = PyCircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            name=name,
        )

        logger.info(
            f"Initialized circuit breaker: {name} "
            f"(fail_max={fail_max}, reset_timeout={reset_timeout}s)"
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        try:
            return self.breaker.call(func, *args, **kwargs)
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker {self.name} is open: {e}")
            raise

    def is_open(self) -> bool:
        """Check if circuit is open.

        Returns:
            True if open, False otherwise
        """
        return self.breaker.current_state == "open"

    def is_closed(self) -> bool:
        """Check if circuit is closed.

        Returns:
            True if closed, False otherwise
        """
        return self.breaker.current_state == "closed"

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.breaker.close()
        logger.info(f"Circuit breaker {self.name} reset to closed")


class CircuitBreakerManager:
    """Manages multiple circuit breakers for different services."""

    def __init__(self):
        """Initialize circuit breaker manager."""
        self.breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        service_name: str,
        fail_max: int = 5,
        reset_timeout: int = 60,
    ) -> CircuitBreaker:
        """Get or create circuit breaker for service.

        Args:
            service_name: Service name
            fail_max: Maximum failures before opening
            reset_timeout: Reset timeout in seconds

        Returns:
            Circuit breaker instance
        """
        if service_name not in self.breakers:
            self.breakers[service_name] = CircuitBreaker(
                name=service_name,
                fail_max=fail_max,
                reset_timeout=reset_timeout,
            )

        return self.breakers[service_name]

    def get_status(self) -> dict[str, str]:
        """Get status of all circuit breakers.

        Returns:
            Dictionary mapping service names to states
        """
        return {
            name: breaker.breaker.current_state
            for name, breaker in self.breakers.items()
        }

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            breaker.reset()
