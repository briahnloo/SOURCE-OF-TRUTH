"""Retry utilities with exponential backoff and detailed error handling

Provides robust retry mechanisms for network operations and API calls with:
- Configurable exponential backoff
- Specific exception categorization (transient vs permanent)
- Structured logging with context
- Jitter to prevent thundering herd
"""

import random
import time
from typing import Callable, List, Optional, Type, TypeVar

from loguru import logger

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (including initial)
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay between retries (cap for exponential backoff)
            exponential_base: Multiplier for exponential backoff (e.g., 2.0 = doubles each time)
            jitter: If True, add random jitter to delays to prevent thundering herd
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed)"""
        if attempt == 0:
            return 0  # No delay on first attempt

        # Exponential backoff: delay = initial_delay * (base ^ (attempt - 1))
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)  # Cap at max_delay

        # Add jitter: random value between 0 and delay
        if self.jitter:
            delay = random.uniform(0, delay)

        return delay


# Transient errors that are worth retrying
TRANSIENT_ERRORS = (
    ConnectionError,
    TimeoutError,
    OSError,  # Includes socket errors
    BrokenPipeError,
)

# HTTP status codes that indicate transient failures
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}

# Permanent errors that should not be retried
PERMANENT_ERRORS = (ValueError, TypeError, KeyError, AttributeError)


def is_transient_error(error: Exception) -> bool:
    """
    Determine if an error is transient (worth retrying) or permanent.

    Transient errors:
    - Network/connection errors
    - Timeouts
    - HTTP 5xx, 429 (rate limit), 408 (timeout)

    Permanent errors:
    - Validation/type errors
    - 4xx (except 408, 429)
    - Application logic errors

    Args:
        error: The exception to check

    Returns:
        True if error is transient and worth retrying
    """
    # Check if it's a known transient exception type
    if isinstance(error, TRANSIENT_ERRORS):
        return True

    # Check for requests.RequestException (covers HTTP errors)
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        status_code = error.response.status_code
        return status_code in TRANSIENT_HTTP_CODES

    # Check if it's a known permanent exception type
    if isinstance(error, PERMANENT_ERRORS):
        return False

    # Default: assume transient (better to retry than fail silently)
    return True


def retry_with_backoff(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    operation_name: str = "operation",
    **kwargs,
) -> T:
    """
    Execute a function with automatic retry and exponential backoff.

    Handles transient failures gracefully with exponential backoff and jitter.

    Args:
        func: Callable to execute
        *args: Positional arguments for func
        config: RetryConfig instance (uses defaults if not provided)
        operation_name: Name for logging (e.g., "fetch_gdelt")
        **kwargs: Keyword arguments for func

    Returns:
        Result of func() if successful

    Raises:
        The final exception if all retries fail

    Examples:
        >>> def fetch_articles():
        ...     return requests.get("https://api.example.com/articles").json()
        >>>
        >>> config = RetryConfig(max_attempts=3, initial_delay=1.0)
        >>> articles = retry_with_backoff(
        ...     fetch_articles,
        ...     config=config,
        ...     operation_name="fetch_gdelt"
        ... )
    """
    if config is None:
        config = RetryConfig()

    last_error = None

    for attempt in range(config.max_attempts):
        try:
            logger.debug(f"{operation_name}: Attempt {attempt + 1}/{config.max_attempts}")
            return func(*args, **kwargs)

        except Exception as e:
            last_error = e
            is_transient = is_transient_error(e)

            # Log the error with appropriate level
            if attempt < config.max_attempts - 1:
                if is_transient:
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"{operation_name}: Transient error on attempt {attempt + 1}, "
                        f"retrying in {delay:.1f}s: {type(e).__name__}: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"{operation_name}: Permanent error (not retrying): "
                        f"{type(e).__name__}: {str(e)}"
                    )
                    raise
            else:
                logger.error(
                    f"{operation_name}: Failed after {config.max_attempts} attempts: "
                    f"{type(e).__name__}: {str(e)}"
                )

    # All retries exhausted
    if last_error:
        raise last_error
    else:
        raise RuntimeError(f"Unknown error in {operation_name}")


class RetryableOperation:
    """Context manager for retry-able operations with detailed tracking"""

    def __init__(
        self,
        operation_name: str,
        config: Optional[RetryConfig] = None,
    ):
        """
        Initialize retry-able operation context.

        Args:
            operation_name: Human-readable name for logging
            config: RetryConfig instance
        """
        self.operation_name = operation_name
        self.config = config or RetryConfig()
        self.attempt = 0
        self.start_time = None
        self.errors: List[tuple] = []

    def __enter__(self):
        """Enter context manager"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and handle errors"""
        if exc_type is None:
            # Success
            duration = time.time() - self.start_time
            logger.info(
                f"{self.operation_name}: Success after {duration:.2f}s "
                f"(attempt {self.attempt + 1}/{self.config.max_attempts})"
            )
            return True

        # Error occurred
        self.attempt += 1
        is_transient = is_transient_error(exc_val)
        self.errors.append((exc_type, exc_val, exc_tb))

        if not is_transient or self.attempt >= self.config.max_attempts:
            # Permanent error or out of retries
            error_type = "permanent" if not is_transient else "transient (out of retries)"
            logger.error(
                f"{self.operation_name}: {error_type} error after {self.attempt} attempts: "
                f"{exc_type.__name__}: {str(exc_val)}"
            )
            return False  # Re-raise the exception

        # Transient error with retries remaining
        delay = self.config.get_delay(self.attempt - 1)
        logger.warning(
            f"{self.operation_name}: Transient error, retrying in {delay:.1f}s "
            f"(attempt {self.attempt}/{self.config.max_attempts}): "
            f"{exc_type.__name__}: {str(exc_val)}"
        )
        time.sleep(delay)
        return True  # Suppress exception


def get_retry_config_for_source(source_name: str) -> RetryConfig:
    """
    Get optimized retry config for a specific data source.

    Different sources have different reliability characteristics:
    - GDELT: Very stable, minimal retries
    - Reddit: Moderate rate limits, more retries
    - RSS: Can have temporary redirects, more retries
    - API sources: Rate limiting, aggressive backoff

    Args:
        source_name: Name of the source (case-insensitive)

    Returns:
        Optimized RetryConfig for the source
    """
    source_lower = source_name.lower()

    if "gdelt" in source_lower:
        return RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=10.0)

    elif "reddit" in source_lower:
        return RetryConfig(max_attempts=4, initial_delay=2.0, max_delay=30.0)

    elif "rss" in source_lower or "feed" in source_lower:
        return RetryConfig(max_attempts=3, initial_delay=1.5, max_delay=20.0)

    elif "newsapi" in source_lower or "mediastack" in source_lower:
        return RetryConfig(max_attempts=3, initial_delay=2.0, max_delay=60.0)

    elif "ngo" in source_lower or "gov" in source_lower or "usgs" in source_lower:
        return RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=15.0)

    else:
        # Default conservative config
        return RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=30.0)
