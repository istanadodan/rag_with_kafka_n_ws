from datetime import datetime
from fastapi import Request, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Callable, Type
from schemas.base import ErrorResponse
from cmn.exception import (
    DatabaseException,
    CommunicationException,
    ValidationException,
    DomainException,
)


def get_exception_handlers() -> dict[Type[Exception], Callable]:
    return {
        DatabaseException: database_exception_handler,
        CommunicationException: communication_exception_handler,
        ValidationException: validation_exception_handler,
        DomainException: domain_exception_handler,
        Exception: unexpected_exception_handler,
    }


# def register_exception_handlers(
#     app: FastAPI,
# ) -> None:
#     handlers = {
#         DatabaseException: database_exception_handler,
#         CommunicationException: communication_exception_handler,
#         ValidationException: validation_exception_handler,
#         DomainException: domain_exception_handler,
#         Exception: unexpected_exception_handler,
#     }

#     for exc_type, handler in handlers.items():
#         app.add_exception_handler(exc_type, handler)


# 공통 에러응답처리
def _error_response(request: Request, exc: Exception, status: int):
    from core.middleware.trace_id import get_trace_id

    body = ErrorResponse(
        # trace_id=getattr(request.state, "trace_id", "-"),
        trace_id=get_trace_id(),
        timestamp=datetime.now(),
        error_type=exc.__class__.__name__,
        message=str(exc),
    )
    return JSONResponse(
        status_code=status, content=jsonable_encoder(body), media_type="json"
    )


# DB관련 오류 전반
def database_exception_handler(request: Request, exc: DatabaseException):
    return _error_response(request, exc, 500)


# 통신API 호출중 오류 전반
def communication_exception_handler(request: Request, exc: CommunicationException):
    return _error_response(request, exc, 502)


# 입력파라미터 유효성오류 처리
def validation_exception_handler(request: Request, exc: ValidationException):
    return _error_response(request, exc, 400)


# 기능처리 중 발생되는 예외
def domain_exception_handler(request: Request, exc: DomainException):
    return _error_response(request, exc, 422)


# 알수없는 예외
def unexpected_exception_handler(request: Request, exc: Exception):
    return _error_response(request, exc, 500)
