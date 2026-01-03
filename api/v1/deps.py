from fastapi import Request
from core.config import settings
from services.store.qdrant_vdb import get_qdrant_client
from repositories.source_repository import SourceRepository
from services.llm.embedding import StudioLmEmbedding
from services.ingest_service import RagIngestService
from services.rag_service import RagQueryService


qdrant = get_qdrant_client()
embedder = StudioLmEmbedding(dim=settings.embedding_dim)
source_repo = SourceRepository()


_rag_ingest_service = RagIngestService(
    qdrant=qdrant,
    embedder=embedder,
    collection=settings.qdrant_collection,
)
_rag_query_service = RagQueryService(
    qdrant=qdrant,
    embedder=embedder,
    collection=settings.qdrant_collection,
)


def _get_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "APP")


# ---- Endpoint DI wiring ----
def _get_ingest_service() -> RagIngestService:
    return _rag_ingest_service


def _get_rag_service() -> RagQueryService:
    return _rag_query_service
