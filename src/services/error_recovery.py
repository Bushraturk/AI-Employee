"""Error Recovery Service for Gold Tier.

Provides retry logic, circuit breaker pattern, action queuing, and graceful
degradation for all external service integrations.
"""

import logging
from pathlib import Path
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime
from functools import wraps
import frontmatter

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from pybreaker import CircuitBreaker, CircuitBreakerError

from src.models.error_recovery_log import (
    ErrorRecoveryLog,
    ErrorType,
    ServiceType,
    RecoveryStrategy,
    RecoveryOutcome
)

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Transient error that should be retried."""
    pass


class PermanentError(Exception):
    """Permanent error that should not be retried."""
    pass


class ErrorRecoveryService:
    """Comprehensive error recovery service with retry, circuit breaker, and queuing.

    Features:
    - Exponential backoff retry (max 3 attempts)
    - Circuit breaker pattern for each service
    - Markdown-based action queue for failed operations
    - Circuit state persistence
    - Graceful degradation after consecutive failures
    - Comprehensive error logging
    """

    def __init__(self, vault_path: Path):
        """Initialize error recovery service.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.failure_counts: Dict[str, int] = {}
        self.disabled_services: set = set()

        # Initialize circuit breakers for each service
        self._initialize_circuit_breakers()

        # Load circuit states from vault
        self._load_circuit_states()

        # Load failure counts
        self._load_failure_counts()

    def _initialize_circuit_breakers(self) -> None:
        """Initialize circuit breakers for all external services."""
        services = [
            ServiceType.ODOO,
            ServiceType.FACEBOOK,
            ServiceType.INSTAGRAM,
            ServiceType.TWITTER,
            ServiceType.LINKEDIN,
            ServiceType.GMAIL,
            ServiceType.WHATSAPP
        ]

        for service in services:
            # Circuit breaker opens after 10 consecutive failures
            # Stays open for 5 minutes (300 seconds)
            # Half-open state allows 1 test request
            breaker = CircuitBreaker(
                fail_max=10,
                timeout_duration=300,
                name=service.value
            )

            # Add state change listeners
            breaker.add_listener(self._on_circuit_open)
            breaker.add_listener(self._on_circuit_close)

            self.circuit_breakers[service.value] = breaker

    def _on_circuit_open(self, breaker: CircuitBreaker, *args, **kwargs) -> None:
        """Handle circuit breaker opening."""
        logger.error(f"Circuit breaker OPENED for {breaker.name} - service temporarily disabled")
        self._persist_circuit_state(breaker.name, "open")

    def _on_circuit_close(self, breaker: CircuitBreaker, *args, **kwargs) -> None:
        """Handle circuit breaker closing."""
        logger.info(f"Circuit breaker CLOSED for {breaker.name} - service restored")
        self._persist_circuit_state(breaker.name, "closed")

    def _persist_circuit_state(self, service: str, state: str) -> None:
        """Persist circuit breaker state to vault.

        Args:
            service: Service name
            state: Circuit state (open/closed/half-open)
        """
        try:
            state_dir = self.vault_path / "Circuit_State"
            state_dir.mkdir(parents=True, exist_ok=True)

            state_file = state_dir / f"{service}_circuit.md"

            metadata = {
                "service": service,
                "state": state,
                "timestamp": datetime.now().isoformat()
            }

            body = f"""# Circuit Breaker State: {service.title()}

**State**: {state.upper()}
**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Description

Circuit breaker is currently **{state.upper()}**.

- **CLOSED**: Service is healthy, requests are allowed
- **OPEN**: Service is failing, requests are blocked
- **HALF-OPEN**: Testing if service has recovered
"""

            post = frontmatter.Post(body, **metadata)
            state_file.write_text(frontmatter.dumps(post), encoding="utf-8")

        except Exception as e:
            logger.error(f"Failed to persist circuit state for {service}: {e}")

    def _load_circuit_states(self) -> None:
        """Load circuit breaker states from vault."""
        state_dir = self.vault_path / "Circuit_State"
        if not state_dir.exists():
            return

        for state_file in state_dir.glob("*_circuit.md"):
            try:
                content = state_file.read_text(encoding="utf-8")
                post = frontmatter.loads(content)

                service = post["service"]
                state = post["state"]

                # Note: Circuit breaker state is managed by pybreaker at runtime
                # This is just for informational purposes on restart
                logger.info(f"Loaded circuit state for {service}: {state}")

            except Exception as e:
                logger.error(f"Failed to load circuit state from {state_file}: {e}")

    def _load_failure_counts(self) -> None:
        """Load failure counts from error recovery logs."""
        log_dir = self.vault_path / "Logs" / "error_recovery"
        if not log_dir.exists():
            return

        # Count recent failures per service (last 24 hours)
        cutoff = datetime.now().timestamp() - (24 * 3600)

        for log_file in log_dir.glob("*.md"):
            try:
                content = log_file.read_text(encoding="utf-8")
                post = frontmatter.loads(content)

                timestamp = datetime.fromisoformat(post["timestamp"])
                if timestamp.timestamp() < cutoff:
                    continue

                service = post["service"]
                outcome = post["outcome"]

                if outcome == "escalated":
                    self.failure_counts[service] = self.failure_counts.get(service, 0) + 1

            except Exception as e:
                logger.error(f"Failed to load failure count from {log_file}: {e}")

        # Check for services that should be disabled
        for service, count in self.failure_counts.items():
            if count >= 10:
                self.disabled_services.add(service)
                logger.warning(f"Service {service} disabled due to {count} consecutive failures")

    def with_retry(self, service: ServiceType, error_type: ErrorType,
                   action_name: str, context: Optional[Dict[str, Any]] = None):
        """Decorator for retry logic with exponential backoff.

        Args:
            service: Service type
            error_type: Error type
            action_name: Name of action being performed
            context: Additional context for logging

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                attempt_timestamps = []

                # Check if service is disabled
                if service.value in self.disabled_services:
                    logger.error(f"Service {service.value} is disabled - queuing action")
                    self._queue_action(service, action_name, args, kwargs, context)
                    raise PermanentError(f"Service {service.value} is disabled")

                # Get circuit breaker for this service
                breaker = self.circuit_breakers.get(service.value)

                @retry(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=4, max=10),
                    retry=retry_if_exception_type(TransientError),
                    before_sleep=before_sleep_log(logger, logging.WARNING),
                    after=after_log(logger, logging.INFO)
                )
                def retry_wrapper():
                    attempt_timestamps.append(datetime.now().isoformat())

                    try:
                        # Check circuit breaker
                        if breaker:
                            with breaker:
                                return func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)

                    except CircuitBreakerError:
                        # Circuit is open, queue the action
                        logger.error(f"Circuit breaker open for {service.value} - queuing action")
                        self._queue_action(service, action_name, args, kwargs, context)
                        raise PermanentError(f"Circuit breaker open for {service.value}")

                    except Exception as e:
                        # Determine if error is transient or permanent
                        if self._is_transient_error(e):
                            raise TransientError(str(e)) from e
                        else:
                            raise PermanentError(str(e)) from e

                try:
                    result = retry_wrapper()

                    # Log successful recovery if there were retries
                    if len(attempt_timestamps) > 1:
                        self._log_recovery(
                            service=service,
                            error_type=error_type,
                            error_message=f"Recovered after {len(attempt_timestamps)} attempts",
                            retry_count=len(attempt_timestamps) - 1,
                            recovery_strategy=RecoveryStrategy.RETRY,
                            outcome=RecoveryOutcome.RECOVERED,
                            context={
                                **(context or {}),
                                "action": action_name,
                                "attempt_timestamps": attempt_timestamps
                            }
                        )

                    return result

                except PermanentError as e:
                    # Log permanent failure
                    self._log_recovery(
                        service=service,
                        error_type=error_type,
                        error_message=str(e),
                        retry_count=0,
                        recovery_strategy=RecoveryStrategy.QUEUE,
                        outcome=RecoveryOutcome.QUEUED,
                        context={**(context or {}), "action": action_name}
                    )
                    raise

                except Exception as e:
                    # Log escalated failure (max retries exhausted)
                    self._log_recovery(
                        service=service,
                        error_type=error_type,
                        error_message=str(e),
                        retry_count=3,
                        recovery_strategy=RecoveryStrategy.ESCALATE,
                        outcome=RecoveryOutcome.ESCALATED,
                        context={
                            **(context or {}),
                            "action": action_name,
                            "attempt_timestamps": attempt_timestamps
                        }
                    )

                    # Increment failure count
                    self._increment_failure_count(service)

                    # Queue the action for later retry
                    self._queue_action(service, action_name, args, kwargs, context)

                    raise

            return wrapper
        return decorator

    def _is_transient_error(self, error: Exception) -> bool:
        """Determine if error is transient and should be retried.

        Args:
            error: Exception to check

        Returns:
            True if error is transient
        """
        error_str = str(error).lower()

        # Network errors
        if any(keyword in error_str for keyword in [
            "timeout", "connection", "network", "unreachable", "refused"
        ]):
            return True

        # Rate limit errors
        if any(keyword in error_str for keyword in [
            "rate limit", "too many requests", "429"
        ]):
            return True

        # Temporary server errors
        if any(keyword in error_str for keyword in [
            "500", "502", "503", "504", "server error", "temporarily unavailable"
        ]):
            return True

        return False

    def _log_recovery(self, service: ServiceType, error_type: ErrorType,
                     error_message: str, retry_count: int,
                     recovery_strategy: RecoveryStrategy,
                     outcome: RecoveryOutcome,
                     context: Optional[Dict[str, Any]] = None) -> None:
        """Log error recovery attempt.

        Args:
            service: Service type
            error_type: Error type
            error_message: Error message
            retry_count: Number of retries
            recovery_strategy: Strategy used
            outcome: Recovery outcome
            context: Additional context
        """
        try:
            log = ErrorRecoveryLog.create(
                error_type=error_type,
                service=service,
                error_message=error_message[:500],  # Truncate to 500 chars
                retry_count=retry_count,
                recovery_strategy=recovery_strategy,
                outcome=outcome,
                context=context
            )

            log.save(self.vault_path)
            logger.info(f"Logged error recovery: {log.error_id}")

        except Exception as e:
            logger.error(f"Failed to log error recovery: {e}")

    def _queue_action(self, service: ServiceType, action_name: str,
                     args: tuple, kwargs: dict, context: Optional[Dict[str, Any]] = None) -> None:
        """Queue failed action for later retry.

        Args:
            service: Service type
            action_name: Action name
            args: Function arguments
            kwargs: Function keyword arguments
            context: Additional context
        """
        try:
            queue_dir = self.vault_path / "Action_Queue"
            queue_dir.mkdir(parents=True, exist_ok=True)

            queue_file = queue_dir / f"{service.value}_queue.md"

            # Load existing queue or create new
            if queue_file.exists():
                content = queue_file.read_text(encoding="utf-8")
                post = frontmatter.loads(content)
                queued_actions = post.get("queued_actions", [])
            else:
                queued_actions = []

            # Add new action to queue
            queued_actions.append({
                "action": action_name,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            })

            metadata = {
                "service": service.value,
                "queue_length": len(queued_actions),
                "last_updated": datetime.now().isoformat(),
                "queued_actions": queued_actions
            }

            body = f"""# Action Queue: {service.value.title()}

**Service**: {service.value.title()}
**Queue Length**: {len(queued_actions)}
**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Queued Actions

{chr(10).join(f"{i+1}. {action['action']} (queued at {action['timestamp']})" for i, action in enumerate(queued_actions))}

## Notes

Actions are queued when the service is unavailable or circuit breaker is open.
They will be retried automatically when the service recovers.
"""

            post = frontmatter.Post(body, **metadata)
            queue_file.write_text(frontmatter.dumps(post), encoding="utf-8")

            logger.info(f"Queued action {action_name} for service {service.value}")

        except Exception as e:
            logger.error(f"Failed to queue action: {e}")

    def _increment_failure_count(self, service: ServiceType) -> None:
        """Increment failure count for service and check for graceful degradation.

        Args:
            service: Service type
        """
        self.failure_counts[service.value] = self.failure_counts.get(service.value, 0) + 1

        # Check if service should be disabled (10 consecutive failures)
        if self.failure_counts[service.value] >= 10:
            self.disabled_services.add(service.value)
            logger.error(
                f"Service {service.value} disabled after {self.failure_counts[service.value]} "
                f"consecutive failures - graceful degradation activated"
            )

            # TODO: Notify user about service degradation
            # This would integrate with notification system

    def get_queue_status(self, service: ServiceType) -> Dict[str, Any]:
        """Get status of action queue for a service.

        Args:
            service: Service type

        Returns:
            Dictionary with queue status
        """
        queue_file = self.vault_path / "Action_Queue" / f"{service.value}_queue.md"

        if not queue_file.exists():
            return {
                "service": service.value,
                "queue_length": 0,
                "queued_actions": []
            }

        try:
            content = queue_file.read_text(encoding="utf-8")
            post = frontmatter.loads(content)

            return {
                "service": service.value,
                "queue_length": post.get("queue_length", 0),
                "queued_actions": post.get("queued_actions", []),
                "last_updated": post.get("last_updated")
            }

        except Exception as e:
            logger.error(f"Failed to get queue status for {service.value}: {e}")
            return {
                "service": service.value,
                "queue_length": 0,
                "queued_actions": [],
                "error": str(e)
            }

    def is_service_available(self, service: ServiceType) -> bool:
        """Check if service is available (not disabled).

        Args:
            service: Service type

        Returns:
            True if service is available
        """
        return service.value not in self.disabled_services
