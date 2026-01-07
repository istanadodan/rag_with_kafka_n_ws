from utils.logging import logging, log_block_ctx
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from services.store.qdrant_store import get_qdrant_vectorstore

logger = logging.getLogger(__name__)


class RetrieverProvider:
    def __init__(self, retriever, retriever_name):
        self.retriever = retriever
        self.retriever_name = retriever_name

    def get_retriever(self):
        return self.retriever

    def get_retriever_name(self):
        return self.retriever_name


# from services.store.qdrant_vdb import get_qdrant_client
# from qdrant_client.http.models import VectorParams, Distance, Bm25Config


def get_retriever(retriever_name, filter, top_k: int, **kwargs) -> BaseRetriever:

    if retriever_name == "qdrant":
        # retriever = QdrantSparseVectorRetriever(
        #     client=qdrant_helper.client,
        #     collection_name="rag_pipeline",
        #     sparse_vector_name="sparse_vector",
        #     sparse_encoder=lambda x: (x, x),
        # )
        # return RetrieverProvider(retriever, retriever_name)
        return get_qdrant_vectorstore().as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k, "filter": filter},
        )
    elif retriever_name == "multiQuery":
        from langchain_classic.retrievers import (
            MultiQueryRetriever,
            multi_query,
        )
        from langchain_classic.prompts import ChatPromptTemplate

        with log_block_ctx(
            logger, f"multiQuery retriever: {multi_query.DEFAULT_QUERY_PROMPT.template}"
        ):
            llm = kwargs.get("llm")
            prompt = ChatPromptTemplate.from_template(
                multi_query.DEFAULT_QUERY_PROMPT.template
            )
            retriever = get_retriever(
                kwargs.get("base_retriever"), filter, top_k, **kwargs
            )
            if not llm:
                raise ValueError("llm is required for multiQuery retriever")

            return MultiQueryRetriever.from_llm(
                llm=llm, retriever=retriever, prompt=prompt
            )
    elif retriever_name == "selfQuery":
        from langchain_classic.retrievers import SelfQueryRetriever
        from langchain_classic.chains.query_constructor.schema import AttributeInfo

        # from langchain_community.retrievers.bm25 import BM25Retriever

        # return BM25Retriever.from_texts(
        #     kwargs.get("texts", ""), metadatas=[{"filter": filter}]
        # )
        # 문서
        metadata_field_info = [
            AttributeInfo(
                name="metadata.publisher",
                description="문서작성자- 배출증관련: Skia/PDF m128",
                type="string",
            ),
            AttributeInfo(
                name="metadata.source",
                description="파일명-배출증관련: /mnt/배출증 출력.pdf",
                type="string",
            ),
        ]
        return SelfQueryRetriever.from_llm(
            llm=kwargs.get("llm", "studio"),
            vectorstore=get_qdrant_vectorstore(),
            # document_content_description="Skia/PDF m128",
            document_contents="배출증 사용 매뉴얼",
            verbose=True,
            metadata_field_info=metadata_field_info,
            search_kwargs={"k": top_k},
        )
    else:
        raise ValueError(f"Unknown retriever name: {retriever_name}")
