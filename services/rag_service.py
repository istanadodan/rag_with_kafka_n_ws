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
        query_vector = self.embedder.embed([query])[0]
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from qdrant_client.conversions.common_types import QueryResponse

        _filter = Filter(
            must=[FieldCondition(key="type", match=MatchValue(value="pdf"))]
        )

        result: QueryResponse = self.qdrant.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            # query_filter=_filter,
            limit=top_k,
            # with_payload=True,
        )

        hits = [
            RagHit(
                score=r.score,
                source=r.payload.get("source", ""),
                metadata={k: v for k, v in r.payload.items() if k != "source"},
            )
            for r in result.points
            if r.payload
        ]

        return QueryByRagResult(
            answer="stub 답변 (LLM 미연동)",
            hits=hits,
        )
