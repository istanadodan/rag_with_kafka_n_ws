import logging
from core.trace_id import get_trace_id


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    fmt = "%(asctime)s %(levelname)s [%(name)s|%(lineno)d] trace_id=%(trace_id)s - %(message)s"
    formatter = logging.Formatter(fmt=fmt)
    handler.setFormatter(formatter)

    handler.addFilter(TraceIdFilter())

    root.handlers.clear()
    root.addHandler(handler)
