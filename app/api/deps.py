from fastapi import Request
from core.config import settings
from core.db import get_qdrant_client
from repositories.source_repository import SourceRepository
from services.llm.embedding import embedding
from services.ingest_service import RagIngestService
from services.rag_service import RagQueryService
from utils.logging import log_block_ctx, logging

logger = logging.getLogger(__name__)

qdrant_vdb = get_qdrant_client()
source_repo = SourceRepository()


_rag_ingest_service = RagIngestService(
    qdrant=qdrant_vdb,
    embedder=embedding,
    collection=settings.qdrant_collection,
)
_rag_query_service = RagQueryService(
    qdrant=qdrant_vdb, embedder=embedding, collection=settings.qdrant_collection
)


def find_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "APP")


# ---- Endpoint DI wiring ----
def get_ingest_service(request: Request | None = None) -> RagIngestService:
    return _rag_ingest_service


def get_rag_service(request: Request) -> RagQueryService:
    return _rag_query_service
