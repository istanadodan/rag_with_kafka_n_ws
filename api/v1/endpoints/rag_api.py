import os
from fastapi import APIRouter, Depends
from fastapi import UploadFile, File
from datetime import datetime
from pathlib import Path
import shutil
from core.config import settings
from api.v1.deps import _get_rag_service, _get_trace_id
from schemas.stomp import StompFrameModel
from schemas.rag import (
    RagPipelineResponse,
    QueryByRagResult,
    QueryByRagRequest,
    QueryByRagResponse,
)
from services.kafka_bridge import KafkaBridge
from services.rag_service import RagQueryService
from utils.logging import logging, log_block_ctx
from starlette.background import BackgroundTask

router = APIRouter()
logger = logging.getLogger(__name__)

# def get_ingest_service() -> RagIngestService:
#     # main.py에서 DI 컨테이너로 묶을 수도 있으나, 템플릿은 단순화를 위해 main에서 주입
#     raise RuntimeError("DI not wired")


# def get_rag_service() -> RagQueryService:
#     raise RuntimeError("DI not wired")


@router.post("/rag-pipeline", response_model=RagPipelineResponse)
async def rag_pipeline(
    trace_id: str = Depends(_get_trace_id), upload_file: UploadFile = File(...)
):
    import cmn.event_loop as el

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
        f = StompFrameModel(
            command="pipeline-start",
            headers={},
            body=os.path.splitext(upload_file.filename)[0],
        )
        # kafkaService.set_event_loop(el.MAIN_LOOP)
        kafka_service.send_message_sync(
            topic=settings.kafka_topic,
            key=trace_id,
            value=f.model_dump(),
        )

    return RagPipelineResponse(
        timestamp=datetime.now(),
        trace_id=trace_id,
        result="OK",
    )


from fastapi.responses import JSONResponse


@router.post("/query_by_rag", response_model=QueryByRagResponse)
async def query_by_rag(
    req: QueryByRagRequest,
    trace_id: str = Depends(_get_trace_id),
    svc: RagQueryService = Depends(_get_rag_service),
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

    # 반환값 설정
    # kafka topic 발행
    from services.kafka_bridge import KafkaBridge

    kafka_service = KafkaBridge()
    topic = settings.kafka_topic
    with log_block_ctx(logger, f"send kafka topic({topic})"):
        f = StompFrameModel(
            command="query-by-rag",
            headers={},
            body=req.model_dump_json(),
        )
        kafka_service.send_message_sync(
            topic=topic,
            key=trace_id,
            value=f.model_dump(),
        )

    def bg_task(_id: str):
        logger.info("Background task executed for trace_id=%s", _id)

    task = BackgroundTask(
        bg_task,
        trace_id,
    )
    return JSONResponse(content={"result": "OK"}, media_type="text", background=task)
