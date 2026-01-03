from schemas.rag import QueryByRagResult, RagHit
from services.qdrant_vdb import QdrantClientProvider
from services.embedding import EmbeddingProvider
from utils.logging import logging, log_block_ctx
from core.config import settings
from typing import cast
from services.llm_provider import llm_provider
import os

logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.openai_api_key


class RagQueryService:
    def __init__(
        self, qdrant: QdrantClientProvider, embedder: EmbeddingProvider, collection: str
    ):
        self.qdrant = qdrant
        self.embedder = embedder
        self.collection = collection
        self.llm = llm_provider.llm

    def chat(
        self,
        query: str,
        filter: dict = dict(producer="ESP Ghostscript 7.07"),
        top_k: int = 3,
    ) -> QueryByRagResult:
        # 프롬프트 생성
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough, RunnableLambda

        template = ChatPromptTemplate(
            messages=[
                (
                    "system",
                    """
You are a professional AI assistant based on Retrieval-Augmented Generation (RAG).
You must answer strictly based on the provided context.

Rules:

1. Do not infer or generate information that is not present in the context.
2. Provide concise, fact-based answers but do not cite the basis.
3. If the information is uncertain or insufficient, explicitly state: “This cannot be confirmed from the provided documents.”
4. When necessary, summarize and present key supporting sentences.
5. Do not use context that is unrelated to the question.

Output format:
* Clear and well-structured sentences
* Avoid unnecessary modifiers and verbose explanations

context:
{context}
""",
                ),
                ("user", "{input}"),
            ]
        )
        retrieval_result = self.retrieve(query, filter, top_k)
        _context = [
            r.metadata.get("page_content", "No context") for r in retrieval_result.hits
        ]
        chain = (
            {
                "context": lambda _: (
                    "\n\n".join(_context) if _context else "No context"
                ),
                "input": RunnablePassthrough(),
                "hits": lambda _: retrieval_result.hits,
            }
            | RunnablePassthrough.assign(
                answer=template
                | RunnableLambda(lambda x: logger.info(f"prompt: {x}") or x)
                | self.llm
                | StrOutputParser()
            )
            # | RunnablePassthrough.assign(
            #     _=lambda x: logger.info("context: %s", x["context"]) or x
            # )
            # | RunnableLambda(
            #     lambda x: QueryByRagResult(
            #         answer=cast(dict, x)["answer"], hits=cast(dict, x)["hits"]
            #     )
            # )
            | RunnableLambda(lambda x: QueryByRagResult(**cast(dict, x)))
        )
        return chain.invoke(input={"query": query, "filter": filter, "top-k": top_k})

    # vectordb에서 유사 정보조회
    def retrieve(
        self,
        query: str,
        filter: dict,
        top_k: int = 5,
    ) -> QueryByRagResult:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from qdrant_client.conversions.common_types import QueryResponse

        query_vector = self.embedder.embed([query])[0]

        _filter = (
            Filter(
                must=[
                    FieldCondition(key=key, match=MatchValue(value=value))
                    for key, value in filter.items()
                ]
            )
            if filter
            else None
        )

        result: QueryResponse = self.qdrant.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            query_filter=_filter,
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
            answer="",
            hits=hits,
        )
