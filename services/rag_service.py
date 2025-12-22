from models.rag import QueryByRagResult, RagHit
from clients.qdrant_vdb import QdrantClientProvider
from services.embedding import EmbeddingProvider


class RagQueryService:
    def __init__(
        self,
        qdrant: QdrantClientProvider,
        embedder: EmbeddingProvider,
        collection: str,
    ):
        self.qdrant = qdrant
        self.embedder = embedder
        self.collection = collection

    def query(self, query: str, top_k: int) -> QueryByRagResult:
        vector = self.embedder.embed([query])[0]

        results = self.qdrant.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
        )

        hits = [
            RagHit(
                score=r.score,
                source=r.payload.get("source", ""),
                metadata={k: v for k, v in r.payload.items() if k != "source"},
            )
            for r in results
        ]

        return QueryByRagResult(
            answer="stub 답변 (LLM 미연동)",
            hits=hits,
        )
