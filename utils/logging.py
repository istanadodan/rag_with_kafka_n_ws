from contextlib import contextmanager
import logging


@contextmanager
def log_block_ctx(logger: logging.Logger, title: str, level: int = logging.INFO):
    sep = "-" * 120
    logger.log(level, "\n%s\n[START] %s\n%s", sep, title, sep)
    try:
        yield
    finally:
        logger.log(level, "\n%s\n[END] %s\n%s", sep, title, sep)
