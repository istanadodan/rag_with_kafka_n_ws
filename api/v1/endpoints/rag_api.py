import os
from fastapi import APIRouter, Depends
from fastapi import UploadFile, File
from datetime import datetime
from pathlib import Path
import shutil
from core.config import settings
from api.v1.deps import _get_rag_service, _get_trace_id
from models.rag import (
    RagPipelineResponse,
    QueryByRagResult,
    QueryByRagRequest,
    QueryByRagResponse,
)
from services.kafka_service import KafkaProducerService
from services.ingest_service import RagIngestService
from services.rag_service import RagQueryService
from utils.logging import logging, log_block_ctx

router = APIRouter()
logger = logging.getLogger(__name__)

# def get_ingest_service() -> RagIngestService:
#     # main.py에서 DI 컨테이너로 묶을 수도 있으나, 템플릿은 단순화를 위해 main에서 주입
#     raise RuntimeError("DI not wired")


# def get_rag_service() -> RagQueryService:
#     raise RuntimeError("DI not wired")


@router.post("/rag-pipeline", response_model=RagPipelineResponse)
def rag_pipeline(
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
    with log_block_ctx(logger, f"send kafka topic({settings.kafka_topic})"):
        kafka_producer = KafkaProducerService(
            bootstrap_servers=settings.kafka_bootstrap_servers
        )
        kafka_producer.send_message(
            topic=settings.kafka_topic,
            key="pdf",
            value=dict(value=os.path.splitext(upload_file.filename)[0]),
        )

    return RagPipelineResponse(
        timestamp=datetime.now(),
        trace_id=trace_id,
        result="OK",
    )


@router.post("/query_by_rag", response_model=QueryByRagResponse)
def query_by_rag(
    req: QueryByRagRequest,
    trace_id: str = Depends(_get_trace_id),
    svc: RagQueryService = Depends(_get_rag_service),
):
    result = svc.query(query=req.query, top_k=req.top_k)
    return QueryByRagResponse(
        timestamp=datetime.now(), trace_id=trace_id, result=result
    )
