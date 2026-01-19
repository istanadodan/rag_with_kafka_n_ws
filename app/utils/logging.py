from contextlib import contextmanager
import logging
from utils.str_util import join_all_params


@contextmanager
def log_block_ctx(logger: logging.Logger, title: str, level: int = logging.INFO):
    sep = "-" * 120
    logger.log(level, "\n%s\n[START] %s\n%s", sep, title, sep)
    try:
        yield
    finally:
        logger.log(level, "\n%s\n[END] %s\n%s", sep, title, sep)


from functools import wraps, partial
import inspect


# log decorator
def log_execution_block(title: str = "", level=logging.INFO):

    def decorator(f):
        logger = logging.getLogger(f.__module__)

        def __logging(prefix, title, *args, **kwargs):
            sep = "-" * 120
            logger.log(
                level,
                f"\n%s\n[{prefix}] %s: %s\n%s",
                sep,
                title or f.__qualname__,
                join_all_params(*args, **kwargs),
                sep,
            )

        log_start = partial(__logging, "START")
        log_end = partial(__logging, "END")

        if inspect.iscoroutinefunction(f):

            @wraps(f)
            async def _awrap(*args, **kwargs):
                log_start(title or f.__qualname__, *args, **kwargs)
                _r = await f(*args, **kwargs)
                log_end(f"{title or f.__qualname__} 응답결과: {_r}")
                return _r

            return _awrap
        else:

            @wraps(f)
            def _wrap(*args, **kwargs):
                log_start(title or f.__qualname__, *args, **kwargs)
                _r = f(*args, **kwargs)
                log_end(f"{title or f.__qualname__} 응답결과: {_r}")

            return _wrap

    return decorator
