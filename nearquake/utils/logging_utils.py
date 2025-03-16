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
    Logs the calling function's name and its filtered arguments.
    
    Inspects the previous stack frame to extract the caller's function name and its arguments,
    excluding "self", "logger", and "level". The information is logged using the provided logger
    at the specified logging level.
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
    Logs an informational message using the provided logger.
    
    Additional positional and keyword arguments are passed directly to the underlying logger.
    """
    logger.info(message, *args, **kwargs)


def log_debug(logger: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Log a debug-level message.
    
    This function logs a message at the debug level using the provided logger.
    Additional positional and keyword arguments are forwarded for message formatting.
    
    :param message: The message to log.
    :param args: Extra positional arguments for message formatting.
    :param kwargs: Extra keyword arguments for message formatting.
    """
    logger.debug(message, *args, **kwargs)


def log_warning(logger: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Logs a warning message with standardized formatting.
    
    Additional positional and keyword arguments are forwarded to the logger.
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
    Log an error message with optional exception details.
    
    :param message: The error message to log.
    :param exc: An optional exception whose traceback will be included in the log output.
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
    Log a critical message.
    
    Logs a message at the critical level using the provided logger. If an exception is supplied,
    its details are appended to the message and exception information is recorded.
    
    :param message: The critical message to log.
    :param exc: Optional exception to include in the log.
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
    Log an API request with standardized formatting and masked sensitive data.
    
    :param api_name: The name of the API being called.
    :param endpoint: The API endpoint being invoked.
    :param params: Optional dictionary of request parameters. Sensitive values (e.g., API keys, tokens, auth details, passwords, secrets) are masked.
    :param level: The logging level to use.
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
    
    :param api_name: The name of the API.
    :param endpoint: The endpoint accessed.
    :param status_code: The HTTP status code of the response.
    :param response_summary: Optional summary of the response.
    :param level: The log level to use (default is logging.DEBUG).
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
    
    :param operation: The type of operation performed (e.g., "INSERT", "SELECT").
    :param table: The name of the database table involved.
    :param details: Optional details about the operation.
    :param level: The log level to use.
    """
    if details:
        logger.log(level, f"DB {operation} on {table} - {details}")
    else:
        logger.log(level, f"DB {operation} on {table}")
