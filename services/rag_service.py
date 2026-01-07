from langchain_core.documents import Document
from schemas.rag import QueryByRagResult, RagHit
from services.store.qdrant_vdb import QdrantClientProvider
from services.llm.embedding import EmbeddingProvider
from utils.logging import logging, log_block_ctx
from core.config import settings
from typing import cast
from services.llm.llm_provider import select_llm
import os

logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.openai_api_key


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
        self.llm = select_llm(settings.llm_model_name)

    # llm_model설정
    def llm_model(self, model_name: str):
        self.llm = select_llm(model_name)

    def chat(
        self,
        query: str,
        filter: dict = {"metadata.producer": "Skia/PDF m128"},
        top_k: int = 3,
        llm_model: str = "studio",
    ) -> QueryByRagResult:
        # 프롬프트 생성
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough, RunnableLambda

        # LLM 모델 선택
        self.llm = select_llm(llm_model)

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
3. If the information is uncertain or insufficient, explicitly state as “This cannot be confirmed from the provided documents.”
4. Do not use context that is unrelated to the question.
5. Must answer in Korean

Output format:
- Clear and well-structured sentences
- Avoid unnecessary modifiers and verbose explanations

Context:
 {context}
""",
                ),
                ("user", "{input}"),
            ]
        )
        retrieval_result = self.retrieve(query, filter, top_k)
        _context = [r.page_content for r in retrieval_result.hits]
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
        filter: dict = {"metadata.producer": "Skia/PDF m128"},
        top_k: int = 5,
    ) -> QueryByRagResult:

        from services.store.retriever import get_retriever

        # from services.store.qdrant_store import get_qdrant_vectorstore
        from qdrant_client.http.models import (
            VectorParams,
            MatchValue,
            FieldCondition,
            Filter,
        )

        # store = get_qdrant_vectorstore()
        _filter = Filter(
            must=(
                [
                    FieldCondition(key=key, match=MatchValue(value=value))
                    for key, value in filter.items()
                ]
                if filter
                else None
            )
        )
        # multiQuery
        retriever = get_retriever(
            "selfQuery", _filter, top_k, base_retriever="qdrant", llm=self.llm
        )
        # docs_with_scores: list[tuple[Document, float]] = (
        #     store.similarity_search_with_score(query=query, k=top_k, filter=_filter)
        # )
        retriever.model_dump()[""]
        docs: list[Document] = retriever.invoke(query)

        # hits = [
        #     RagHit(
        #         page_content=doc.page_content,
        #         score=score,
        #         source=doc.metadata["source"],
        #         metadata={k: v for k, v in doc.metadata.items() if k != "source"},
        #     )
        #     for doc, score in docs_with_scores
        # ]
        hits = [
            RagHit(
                page_content=doc.page_content,
                score=0.0,
                source=doc.metadata["source"],
                metadata={k: v for k, v in doc.metadata.items() if k != "source"},
            )
            for doc in docs
        ]

        return QueryByRagResult(
            answer="",
            hits=hits,
        )

    def retrieve2(
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
                page_content=r.payload["page_content"],
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
