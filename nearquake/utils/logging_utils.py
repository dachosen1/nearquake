"""
Logging utilities for the nearquake project.

This module provides standardized logging functions and constants to ensure
consistent logging across all modules in the project.
"""

import inspect
import logging
from typing import Any, Dict, Optional

# ANSI color codes for terminal output
COLORS = {
    "RESET": "\033[0m",
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}

# Log level constants
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for the specified module.

    :param module_name: The name of the module (__name__).
    :return: A configured logger instance.
    """
    return logging.getLogger(module_name)


def log_function_call(logger: logging.Logger, level: int = logging.DEBUG) -> None:
    """
    Log the name of the calling function with its arguments.

    :param logger: The logger instance.
    :param level: The log level to use.
    """
    frame = inspect.currentframe().f_back
    func_name = frame.f_code.co_name
    args = inspect.getargvalues(frame)

    # Filter out 'self' and 'logger' from the arguments
    arg_dict = {
        k: v for k, v in args.locals.items() if k not in ("self", "logger", "level")
    }

    logger.log(level, f"Called {func_name} with args: {arg_dict}")


def log_info(logger: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Log an info message with standardized formatting.

    :param logger: The logger instance.
    :param message: The message to log.
    :param args: Additional positional arguments for the logger.
    :param kwargs: Additional keyword arguments for the logger.
    """
    logger.info(message, *args, **kwargs)


def log_debug(logger: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Log a debug message with standardized formatting.

    :param logger: The logger instance.
    :param message: The message to log.
    :param args: Additional positional arguments for the logger.
    :param kwargs: Additional keyword arguments for the logger.
    """
    logger.debug(message, *args, **kwargs)


def log_warning(logger: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Log a warning message with standardized formatting.

    :param logger: The logger instance.
    :param message: The message to log.
    :param args: Additional positional arguments for the logger.
    :param kwargs: Additional keyword arguments for the logger.
    """
    logger.warning(message, *args, **kwargs)


def log_error(
    logger: logging.Logger,
    message: str,
    exc: Optional[Exception] = None,
    *args,
    **kwargs,
) -> None:
    """
    Log an error message with standardized formatting.

    :param logger: The logger instance.
    :param message: The message to log.
    :param exc: Optional exception to include.
    :param args: Additional positional arguments for the logger.
    :param kwargs: Additional keyword arguments for the logger.
    """
    if exc:
        # If an exception is provided, include it in the message and add exc_info
        logger.error(f"{message}: {exc}", *args, exc_info=True, **kwargs)
    else:
        logger.error(message, *args, **kwargs)


def log_critical(
    logger: logging.Logger,
    message: str,
    exc: Optional[Exception] = None,
    *args,
    **kwargs,
) -> None:
    """
    Log a critical message with standardized formatting.

    :param logger: The logger instance.
    :param message: The message to log.
    :param exc: Optional exception to include.
    :param args: Additional positional arguments for the logger.
    :param kwargs: Additional keyword arguments for the logger.
    """
    if exc:
        # If an exception is provided, include it in the message and add exc_info
        logger.critical(f"{message}: {exc}", *args, exc_info=True, **kwargs)
    else:
        logger.critical(message, *args, **kwargs)


def log_api_request(
    logger: logging.Logger,
    api_name: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    level: int = logging.DEBUG,
) -> None:
    """
    Log an API request with standardized formatting.

    :param logger: The logger instance.
    :param api_name: The name of the API being called.
    :param endpoint: The endpoint being called.
    :param params: Optional parameters being sent with the request.
    :param level: The log level to use.
    """
    # Mask sensitive data in parameters
    if params:
        masked_params = {}
        for key, value in params.items():
            if any(
                pattern in key.lower()
                for pattern in ["api_key", "token", "auth", "password", "secret"]
            ):
                masked_params[key] = "********"
            else:
                masked_params[key] = value
    else:
        masked_params = None

    if params:
        logger.log(
            level,
            f"API Request to {api_name} - Endpoint: {endpoint}, Params: {masked_params}",
        )
    else:
        logger.log(level, f"API Request to {api_name} - Endpoint: {endpoint}")


def log_api_response(
    logger: logging.Logger,
    api_name: str,
    endpoint: str,
    status_code: int,
    response_summary: Optional[str] = None,
    level: int = logging.DEBUG,
) -> None:
    """
    Log an API response with standardized formatting.

    :param logger: The logger instance.
    :param api_name: The name of the API being called.
    :param endpoint: The endpoint being called.
    :param status_code: The HTTP status code of the response.
    :param response_summary: Optional summary of the response.
    :param level: The log level to use.
    """
    if response_summary:
        logger.log(
            level,
            f"API Response from {api_name} - Endpoint: {endpoint}, Status: {status_code}, Summary: {response_summary}",
        )
    else:
        logger.log(
            level,
            f"API Response from {api_name} - Endpoint: {endpoint}, Status: {status_code}",
        )


def log_db_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    details: Optional[str] = None,
    level: int = logging.DEBUG,
) -> None:
    """
    Log a database operation with standardized formatting.

    :param logger: The logger instance.
    :param operation: The operation being performed (e.g., "INSERT", "SELECT").
    :param table: The table being operated on.
    :param details:  Optional details about the operation.
    :param level: The log level to use.
    """
    if details:
        logger.log(level, f"DB {operation} on {table} - {details}")
    else:
        logger.log(level, f"DB {operation} on {table}")
