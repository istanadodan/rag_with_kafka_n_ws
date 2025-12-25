from services.qdrant_vdb import QdrantClientProvider
from repositories.source_repository import SourceRepository
from services.embedding import StudioLmEmbedding
from services.ingest_service import RagIngestService
from services.rag_service import RagQueryService
from core.config import settings
from fastapi import Request

# ---- Infra wiring ----
qdrant = QdrantClientProvider(
    url=settings.qdrant_url, port=settings.qdrant_port, api_key=settings.qdrant_api_key
)
qdrant.ensure_collection(settings.qdrant_collection, settings.embedding_dim)

embedder = StudioLmEmbedding(dim=settings.embedding_dim)
source_repo = SourceRepository()

ingest_svc = RagIngestService(
    qdrant=qdrant,
    embedder=embedder,
    collection=settings.qdrant_collection,
)
rag_svc = RagQueryService(
    qdrant=qdrant,
    embedder=embedder,
    collection=settings.qdrant_collection,
)


def _get_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "APP")


# ---- Endpoint DI wiring ----
def _get_ingest_service() -> RagIngestService:
    return ingest_svc


def _get_rag_service() -> RagQueryService:
    return rag_svc
