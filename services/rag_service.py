from langchain_core.documents import Document
from services.dto.rag import QueryByRagResult, RagHit
from services.vdb.qdrant_client import QdrantClientProvider
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
        retriever_name: str = "qdrant",
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
You are a professional AI assistant operating under a strict Retrieval-Augmented Generation (RAG) policy.

You must answer only using the information explicitly contained in the provided context.
Do not add explanations, examples, code blocks, or meta commentary.

Rules:
- Context에 명시적으로 존재하지 않는 내용은 절대 추론하거나 생성하지 마십시오.
- 답변은 사실 중심의 단문으로 작성하십시오.
- 정보가 없거나 불확실한 경우, 반드시 다음 문장만 출력하십시오:
  - “제공된 문서에서 확인할 수 없습니다.”
- 질문과 직접적으로 관련 없는 Context는 사용하지 마십시오.
- 반드시 한국어로만 답변하십시오.
- 답변 외의 텍스트(설명, 헤더, 마크다운, 코드, 인용 등)는 출력하지 마십시오.

Output Constraints:
- 순수 텍스트 문장만 출력
- 코드 블록, 마크다운, 특수 태그(``` , < > 등) 사용 금지
- 한 문단 이내로 간결하게 작성

Context:
{context}
""",
                ),
                ("user", "{input}"),
            ]
        )
        retrieval_result = self.retrieve(retriever_name, query, filter, top_k)
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
        name: str,
        query: str,
        filter: dict = {"metadata.producer": "Skia/PDF m128"},
        top_k: int = 5,
    ) -> QueryByRagResult:

        from services.vdb.retriever import get_retriever

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
            name, _filter, top_k, base_retriever="qdrant", llm=self.llm
        )
        # docs_with_scores: list[tuple[Document, float]] = (
        #     store.similarity_search_with_score(query=query, k=top_k, filter=_filter)
        # )
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
