"""Shared logging utilities."""

import logging
import time


def setup_logger(name: str) -> logging.Logger:
    """
    Set up logging configuration.

    Returns:
        logging.Logger: Configured logger instance
    """

    # Create custom formatter for UTC timestamps with microseconds
    class UTCFormatter(logging.Formatter):
        def formatTime(
            self, record: logging.LogRecord, datefmt: str | None = None
        ) -> str:
            dt = time.gmtime(record.created)
            microseconds = int((record.created % 1) * 1_000_000)
            return time.strftime("%Y-%m-%dT%H:%M:%S", dt) + f".{microseconds:06d}Z"

    # Configure logging with custom formatter
    handler = logging.StreamHandler()
    formatter = UTCFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Set up logger instance
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger
