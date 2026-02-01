from contextlib import contextmanager
import logging
from utils.str_util import join_all_params
from functools import wraps, partial
import inspect
from typing import Callable, TypeVar, ParamSpec


def get_logger(name: str):
    return logging.getLogger(name)


@contextmanager
def log_block_ctx(logger: logging.Logger, title: str, level: int = logging.INFO):
    sep = "-" * 120
    logger.log(level, "\n%s\n[START] %s\n%s", sep, title, sep)
    try:
        yield
    finally:
        logger.log(level, "\n%s\n[END] %s\n%s", sep, title, sep)


# log decorator
P = ParamSpec("P")
R = TypeVar("R")


def log_execution_block(
    _func: Callable[P, R] | None = None, *, title: str = "", level=logging.INFO
):

    def decorator(f):
        logger = logging.getLogger(f.__module__)

        def __logging(prefix, msg, *args, **kwargs):
            sep = "-" * 120
            logger.log(
                level,
                f"\n%s\n[{prefix}] %s: %s\n%s",
                sep,
                msg,
                join_all_params(*args, **kwargs),
                sep,
            )

        log_start = partial(__logging, "START")
        log_end = partial(__logging, "END")

        if inspect.iscoroutinefunction(f):

            @wraps(f)
            async def _awrap(*args, **kwargs):
                msg = title or f.__qualname__
                log_start(msg, *args, **kwargs)
                _r = await f(*args, **kwargs)
                log_end(f"{msg} 응답결과: {_r}")
                return _r

            return _awrap
        else:

            @wraps(f)
            def _wrap(*args, **kwargs):
                msg = title or f.__qualname__
                log_start(msg, *args, **kwargs)
                _r = f(*args, **kwargs)
                log_end(f"{msg} 응답결과: {_r}")
                return _r

            return _wrap

    # ✅ 괄호 없이 사용: @log_execution_block
    if callable(_func):
        return decorator(_func)

    # ✅ 괄호 포함 사용: @log_execution_block(...)
    return decorator
