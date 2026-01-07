import os
from fastapi import APIRouter, Depends, UploadFile, File
from datetime import datetime
from pathlib import Path
import shutil
from starlette.background import BackgroundTask
from fastapi.responses import JSONResponse
from core.config import settings
from api.v1.deps import _get_rag_service, _get_trace_id
from schemas.stomp import StompFrameModel
from schemas.rag import (
    RagPipelineResponse,
    QueryByRagResult,
    QueryByRagRequest,
    QueryByRagResponse,
)

from services.kafka.kafka_bridge import KafkaBridge
from services.rag_service import RagQueryService
from utils.logging import logging, log_block_ctx


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/rag-pipeline", response_model=RagPipelineResponse)
async def rag_pipeline(
    trace_id: str = Depends(_get_trace_id), upload_file: UploadFile = File(...)
):
    # trace id 취득
    logger.info(
        "content_type=%s, upload_file=%s, trace_id=%s",
        upload_file.content_type,
        upload_file.filename,
        trace_id,
    )
    # 파일 타입 검증
    if (
        upload_file.content_type != "application/pdf"
        or upload_file.filename is None
        or not upload_file.filename.lower().endswith(".pdf")
    ):
        raise ValueError("Only PDF files are allowed.")

    # 파일 저장
    file_path = Path(settings.pdf_dir) / upload_file.filename
    logger.info("file_path=%s", file_path)
    with file_path.open("wb") as f:
        shutil.copyfileobj(upload_file.file, f)

    # 카프카 토픽 생성 - 파이프라인 개시
    kafka_service = KafkaBridge()
    with log_block_ctx(logger, f"send kafka topic({settings.kafka_topic})"):
        # topic발행
        kafka_service.send_message_sync(
            topic=settings.kafka_topic,
            key=trace_id,
            value=StompFrameModel(
                command="pipeline-start",
                headers={},
                body=os.path.splitext(upload_file.filename)[0],
            ).model_dump(),
        )

    return RagPipelineResponse(
        timestamp=datetime.now(),
        trace_id=trace_id,
        result="OK",
    )


@router.post("/search_db", response_model=QueryByRagResult)
async def search_db(
    query: str,
    filter: dict,
    top_k: int = 3,
    trace_id: str = Depends(_get_trace_id),
    svc: RagQueryService = Depends(_get_rag_service),
):
    with log_block_ctx(logger, f"search_db: {query},{filter},{top_k}"):
        result: QueryByRagResult = svc.retrieve(query=query, filter=filter, top_k=top_k)
        return JSONResponse(
            content={
                "result": result.answer,
                "hits": [h.model_dump() for h in result.hits],
                "traceId": trace_id,
            },
            media_type="text",
        )


@router.post("/query_by_rag", response_model=QueryByRagResponse)
async def query_by_rag(
    req: QueryByRagRequest,
    trace_id: str = Depends(_get_trace_id),
):
    """
    Docstring for query_by_rag

    :param req: Description
    :type req: QueryByRagRequest
    :param trace_id: Description
    :type trace_id: str
    :param svc: Description
    :type svc: RagQueryService
    # 절차
    1. query를 vectordb에서 조회
    2. 프롬프트에 context로 포함
    3. 답변생성요청
    4. 사용된 토큰량을 포함해 반환
    """

    # kafka topic 발행
    kafka_service = KafkaBridge()
    topic = settings.kafka_topic
    with log_block_ctx(logger, f"send kafka topic({topic})"):
        kafka_service.send_message_sync(
            topic=topic,
            key=trace_id,
            value=StompFrameModel(
                command="query-by-rag",
                headers={},
                body=req.model_dump_json(),
            ).model_dump(),
        )

    def bg_task(_id: str):
        logger.info("Background task executed for trace_id=%s", _id)

    return JSONResponse(
        content={"result": "OK"},
        media_type="text",
        background=BackgroundTask(
            bg_task,
            trace_id,
        ),
    )
