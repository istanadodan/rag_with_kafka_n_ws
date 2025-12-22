import uuid
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

TRACE_ID_HEADER = "X-Trace-Id"
# app 기동 및 background처리는 APP으로 설정
_trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="APP")


def get_trace_id() -> str:
    return _trace_id_ctx.get()


async def trace_id_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    token = _trace_id_ctx.set(trace_id)
    try:
        response: Response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response
    finally:
        _trace_id_ctx.reset(token)


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        token = _trace_id_ctx.set(trace_id)
        try:
            response: Response = await call_next(request)
            response.headers[TRACE_ID_HEADER] = trace_id
            return response
        finally:
            _trace_id_ctx.reset(token)
