import time
from fastapi import Request
import logging

# from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


async def access_logging_middleware(request: Request, call_next):
    logger.info("Request: %s %s", request.method, request.url.path)
    if request.url.path in ["/docs", "/openapi.json"]:
        return await call_next(request)

    start_time = time.perf_counter()
    try:
        body_bytes = await request.body()
        body = body_bytes.decode("utf-8") if body_bytes else ""
    except Exception:
        body = "<unreadable>"

    logger.info(
        "[REQUEST] %s %s body=%s",
        request.method,
        request.url.path,
        body,
    )

    response = await call_next(request)

    if hasattr(response, "body_iterator"):
        # streaming 방지용 요약
        logger.info(
            "[RESPONSE] %s status=%s elapsed=%.6f sec",
            request.url.path,
            response.status_code,
            time.perf_counter() - start_time,
        )
    else:
        logger.info(
            "[RESPONSE] %s status=%s elapsed=%.6f sec",
            request.url.path,
            response.status_code,
            time.perf_counter() - start_time,
        )

    return response


# class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         logger.info("Request: %s %s", request.method, request.url.path)
#         if request.url.path in ["/docs", "/openapi.json"]:
#             return await call_next(request)
#         # try:
#         #     body_bytes = await request.body()
#         #     body = body_bytes.decode("utf-8") if body_bytes else ""
#         # except Exception:
#         #     body = "<unreadable>"
#         body = "reqeust"
#         logger.info(
#             "[REQUEST] %s %s body=%s",
#             request.method,
#             request.url.path,
#             body,
#         )

#         response = await call_next(request)

#         if hasattr(response, "body_iterator"):
#             # streaming 방지용 요약
#             logger.info(
#                 "[RESPONSE] %s status=%s",
#                 request.url.path,
#                 response.status_code,
#             )
#         else:
#             logger.info(
#                 "[RESPONSE] %s status=%s",
#                 request.url.path,
#                 response.status_code,
#             )

#         return response
