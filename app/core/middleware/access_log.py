import time
from fastapi import Request, Response
import logging

logger = logging.getLogger(__name__)


async def access_logging_middleware(request: Request, call_next):
    if any([x in request.url.path for x in ["/docs", "/openapi.json"]]):
        # swagger ui 제외
        return await call_next(request)

    start_time = time.perf_counter()
    try:
        # body 추출 후 재세팅 처리
        req_body = await _get_req_body_bytes(request)
    except Exception as e:
        req_body = f"<unreadable> {str(e)}"

    logger.info(
        "[REQUEST] %s %s req param=%s",
        request.method,
        request.url.path,
        req_body,
    )

    response = await call_next(request)

    if hasattr(response, "body_iterator"):
        # streaming 방지용 요약
        res_body = await _get_resp_body(response)
    else:
        res_body = response.body

    logger.info(
        "[RESPONSE] %s status=%s elapsed=%.6f sec, resp:%s",
        request.url.path,
        response.status_code,
        time.perf_counter() - start_time,
        res_body,
    )

    return response


# request에서 파라미터 추출
async def _get_req_body_bytes(request: Request) -> str:
    body: bytes = await request.body()

    async def receive():
        return {"type": "http.request", "body": body}

    # 원데이터 복원
    request._receive = receive
    try:
        _r = (
            # body.decode("utf-8", errors="replace")
            body.decode("utf-8", errors="strict")
            if isinstance(body, bytes)
            else str(body) or ""
        )
    except UnicodeDecodeError as e:
        # multipart/form-data 등 바이너리 데이터
        _r = f"[{len(body)} bytes] non-text body"
    return _r


# response에서 반환값 추출
async def _get_resp_body(response) -> str:
    chunk_lst = []
    async for chunk in response.body_iterator:
        chunk_lst.append(chunk)
    body = b"".join(chunk_lst)

    # body_iterator를 bytes로 덮는 대신, generator로 복구
    async def _body_iterator(chunks):
        for chunk in chunks:
            yield chunk

    response.body_iterator = _body_iterator(chunk_lst)

    return body.decode("utf-8") or ""


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
