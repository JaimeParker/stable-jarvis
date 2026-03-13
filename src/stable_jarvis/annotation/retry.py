"""
Retry utilities with exponential backoff for network operations.

Provides decorators and utilities for handling transient failures in
Zotero API calls and other network operations.
"""

from __future__ import annotations

import functools
import random
import ssl
import time
from typing import Any, Callable, Tuple, Type, TypeVar

# Type variable for generic function return type
F = TypeVar("F", bound=Callable[..., Any])


# Default retryable exceptions (network-related errors)
DEFAULT_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    ssl.SSLError,
)

# Try to include httpx exceptions if available
try:
    import httpx
    DEFAULT_RETRYABLE_EXCEPTIONS = DEFAULT_RETRYABLE_EXCEPTIONS + (
        httpx.ConnectError,
        httpx.ReadTimeout,
        httpx.WriteTimeout,
        httpx.ConnectTimeout,
        httpx.PoolTimeout,
    )
except ImportError:
    pass

# Try to include requests exceptions if available
try:
    import requests.exceptions
    DEFAULT_RETRYABLE_EXCEPTIONS = DEFAULT_RETRYABLE_EXCEPTIONS + (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.SSLError,
    )
except ImportError:
    pass


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] | None = None,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts (not including initial try).
            base_delay: Initial delay in seconds before first retry.
            max_delay: Maximum delay in seconds between retries.
            exponential_base: Base for exponential backoff (delay * base^attempt).
            jitter: If True, add random jitter to delays to avoid thundering herd.
            retryable_exceptions: Tuple of exception types to retry on.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or DEFAULT_RETRYABLE_EXCEPTIONS
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.
        
        Args:
            attempt: The retry attempt number (0-indexed).
        
        Returns:
            Delay in seconds.
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add ±25% jitter
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


# Default configuration
DEFAULT_RETRY_CONFIG = RetryConfig()


def retry_with_backoff(
    config: RetryConfig | None = None,
    on_retry: Callable[[Exception, int, float], None] | None = None,
) -> Callable[[F], F]:
    """
    Decorator that adds retry logic with exponential backoff.
    
    Args:
        config: RetryConfig instance. Uses DEFAULT_RETRY_CONFIG if None.
        on_retry: Optional callback called before each retry.
            Receives (exception, attempt_number, delay).
    
    Returns:
        Decorated function that will retry on transient failures.
    
    Example:
        @retry_with_backoff()
        def call_api():
            return requests.get("https://api.example.com")
        
        # With custom config
        @retry_with_backoff(RetryConfig(max_retries=5, base_delay=2.0))
        def call_flaky_api():
            ...
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt >= config.max_retries:
                        # No more retries
                        raise
                    
                    delay = config.get_delay(attempt)
                    
                    if on_retry:
                        on_retry(e, attempt + 1, delay)
                    
                    time.sleep(delay)
            
            # Should not reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")
        
        return wrapper  # type: ignore[return-value]
    
    return decorator


def retry_on_exception(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] | None = None,
) -> Callable[[F], F]:
    """
    Simplified retry decorator with common defaults.
    
    Args:
        max_retries: Maximum retry attempts.
        base_delay: Initial delay in seconds.
        exceptions: Exception types to retry on.
    
    Example:
        @retry_on_exception(max_retries=3)
        def upload_to_zotero():
            ...
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        retryable_exceptions=exceptions or DEFAULT_RETRYABLE_EXCEPTIONS,
    )
    return retry_with_backoff(config)


class RetryContext:
    """
    Context manager for manual retry logic.
    
    Useful when you need more control over the retry process.
    
    Example:
        with RetryContext(max_retries=3) as ctx:
            for attempt in ctx:
                try:
                    result = call_api()
                    break
                except ConnectionError as e:
                    ctx.handle_error(e)
    """
    
    def __init__(self, config: RetryConfig | None = None):
        self.config = config or DEFAULT_RETRY_CONFIG
        self._attempt = 0
        self._last_error: Exception | None = None
    
    def __enter__(self) -> "RetryContext":
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        # Don't suppress exceptions
        return False
    
    def __iter__(self) -> "RetryContext":
        self._attempt = 0
        return self
    
    def __next__(self) -> int:
        if self._attempt > self.config.max_retries:
            if self._last_error:
                raise self._last_error
            raise StopIteration
        
        attempt = self._attempt
        self._attempt += 1
        return attempt
    
    def handle_error(self, error: Exception) -> None:
        """
        Handle an error during retry.
        
        If this is a retryable error and we have retries left,
        wait and continue. Otherwise, re-raise.
        """
        if not isinstance(error, self.config.retryable_exceptions):
            raise error
        
        self._last_error = error
        
        if self._attempt > self.config.max_retries:
            raise error
        
        delay = self.config.get_delay(self._attempt - 1)
        time.sleep(delay)
    
    @property
    def attempt(self) -> int:
        """Current attempt number (0-indexed)."""
        return self._attempt - 1
