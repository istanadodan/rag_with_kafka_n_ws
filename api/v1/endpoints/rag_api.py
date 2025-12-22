import os
from fastapi import APIRouter, Depends
from fastapi import UploadFile, File
from datetime import datetime
from pathlib import Path
import logging
import shutil
from core.config import settings
from api.v1.deps import _get_ingest_service, _get_rag_service
from models.rag import (
    RagPipelineResponse,
    QueryByRagResult,
    QueryByRagRequest,
    QueryByRagResponse,
)
from services.kafka_service import KafkaProducerService
from services.ingest_service import RagIngestService
from services.rag_service import RagQueryService

router = APIRouter()
logger = logging.getLogger(__name__)

# def get_ingest_service() -> RagIngestService:
#     # main.py에서 DI 컨테이너로 묶을 수도 있으나, 템플릿은 단순화를 위해 main에서 주입
#     raise RuntimeError("DI not wired")


# def get_rag_service() -> RagQueryService:
#     raise RuntimeError("DI not wired")


@router.post("/rag-pipeline", response_model=RagPipelineResponse)
def rag_pipeline(
    upload_file: UploadFile = File(...),
    svc: RagIngestService = Depends(_get_ingest_service),
):
    # 파일 타입 검증
    logger.info(
        "content_type=%s, upload_file=%s",
        upload_file.content_type,
        upload_file.filename,
    )
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
    kafka_producer = KafkaProducerService(
        bootstrap_servers=settings.kafka_bootstrap_servers
    )
    kafka_producer.send_message(
        topic=settings.kafka_topic,
        message={"key": "pdf", "value": os.path.splitext(upload_file.filename)[0]},
    )
    logger.info(f"complete to publish kafka topic({settings.kafka_topic})")

    return RagPipelineResponse(timestamp=datetime.now(), trace_id="1", result="ok")


@router.post("/query_by_rag", response_model=QueryByRagResponse)
def query_by_rag(
    req: QueryByRagRequest, svc: RagQueryService = Depends(_get_rag_service)
):
    result = svc.query(query=req.query, top_k=3)
    return QueryByRagResponse(timestamp=datetime.now(), trace_id="1", result=result)
