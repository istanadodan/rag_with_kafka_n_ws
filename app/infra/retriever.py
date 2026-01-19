from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from infra.db import qdrant, postgre
from utils.logging import logging, log_block_ctx
from langchain_classic.retrievers import (
    MultiQueryRetriever,
    multi_query,
    ParentDocumentRetriever,
)
from langchain_classic.prompts import ChatPromptTemplate
from langchain_classic.retrievers import SelfQueryRetriever
from langchain_classic.chains.query_constructor.schema import AttributeInfo
from typing import cast
from langchain_classic.retrievers.multi_vector import SearchType
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.db.rdb import get_rdb

logger = logging.getLogger(__name__)


class RetrieverFactory:
    def __init__(self, retriever_name: str, filter, top_k: int):
        self.retriever_name = retriever_name
        self.filter = filter
        self.top_k = top_k

    def create(self, **kwargs) -> BaseRetriever:
        retrievers = {
            "qdrant": self.qdrant_retriever,
            "multiQuery": self.multi_query_retriever,
            "selfQuery": self.self_query_retriever,
            "parentDocument": self.parent_document_retriever,
        }
        retriever = retrievers.get(self.retriever_name, None)
        if retriever is None:
            raise ValueError(f"Unknown retriever: {self.retriever_name}")
        return cast(BaseRetriever, retriever(**kwargs))

    @log_block_ctx(logger, "qdrant_retriever")
    def qdrant_retriever(self, **kwargs) -> BaseRetriever:
        return qdrant.get_vectorstore().as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k, "filter": self.filter},
        )

    @log_block_ctx(logger, "multiQuery retriever")
    def multi_query_retriever(self, **kwargs) -> BaseRetriever:

        if not (llm := kwargs.get("llm")):
            raise ValueError("llm is required for multiQuery retriever")

        # base retriever
        retriever = RetrieverFactory("qdrant", self.filter, self.top_k).create(**kwargs)

        prompt = ChatPromptTemplate.from_template(
            multi_query.DEFAULT_QUERY_PROMPT.template
        )

        return MultiQueryRetriever.from_llm(llm=llm, retriever=retriever, prompt=prompt)

    @log_block_ctx(logger, "selfQuery retriever")
    def self_query_retriever(self, **kwargs) -> BaseRetriever:

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
            vectorstore=qdrant.get_vectorstore(),
            # document_content_description="Skia/PDF m128",
            document_contents="배출증 사용 매뉴얼",
            verbose=True,
            metadata_field_info=metadata_field_info,
            search_kwargs={"k": self.top_k},
        )

    @log_block_ctx(logger, "parentDocument retriever")
    def parent_document_retriever(self, **kwargs) -> BaseRetriever:
        if not (kwargs.get("child_splitter") and kwargs.get("parent_splitter")):
            raise ValueError("child_splitter and parent_splitter is required")
        # parent store용
        with get_rdb() as session:
            doc_store = postgre.PostgresDocStore(conn=session)

        if doc_store is None:
            raise ValueError("doc_store is required for parentDocument retriever")

        retriever = ParentDocumentRetriever(
            vectorstore=qdrant.get_vectorstore(),
            docstore=doc_store,
            id_key="parent_id",
            child_splitter=kwargs.get("child_splitter", ""),
            parent_splitter=kwargs.get("parent_splitter", ""),
            search_type=SearchType.similarity,
            search_kwargs={"k": self.top_k},
        )

        logging.info(f"parent document retriever called: {doc_store.mget(["48"])}")

        return retriever


# def get_retriever(retriever_name, filter, top_k: int, **kwargs) -> BaseRetriever:

#     if retriever_name == "qdrant":
#         # retriever = QdrantSparseVectorRetriever(
#         #     client=qdrant_helper.client,
#         #     collection_name="rag_pipeline",
#         #     sparse_vector_name="sparse_vector",
#         #     sparse_encoder=lambda x: (x, x),
#         # )
#         # return RetrieverProvider(retriever, retriever_name)
#         return qdrant.get_vectorstore().as_retriever(
#             search_type="similarity",
#             search_kwargs={"k": top_k, "filter": filter},
#         )
#     elif retriever_name == "multiQuery":
#         from langchain_classic.retrievers import (
#             MultiQueryRetriever,
#             multi_query,
#         )
#         from langchain_classic.prompts import ChatPromptTemplate

#         with log_block_ctx(
#             logger, f"multiQuery retriever: {multi_query.DEFAULT_QUERY_PROMPT.template}"
#         ):
#             llm = kwargs.get("llm")
#             prompt = ChatPromptTemplate.from_template(
#                 multi_query.DEFAULT_QUERY_PROMPT.template
#             )
#             retriever = get_retriever(
#                 kwargs.get("base_retriever"), filter, top_k, **kwargs
#             )
#             if not llm:
#                 raise ValueError("llm is required for multiQuery retriever")

#             return MultiQueryRetriever.from_llm(
#                 llm=llm, retriever=retriever, prompt=prompt
#             )
#     elif retriever_name == "selfQuery":
#         from langchain_classic.retrievers import SelfQueryRetriever
#         from langchain_classic.chains.query_constructor.schema import AttributeInfo

#         # from langchain_community.retrievers.bm25 import BM25Retriever

#         # return BM25Retriever.from_texts(
#         #     kwargs.get("texts", ""), metadatas=[{"filter": filter}]
#         # )
#         # 문서
#         metadata_field_info = [
#             AttributeInfo(
#                 name="metadata.publisher",
#                 description="문서작성자- 배출증관련: Skia/PDF m128",
#                 type="string",
#             ),
#             AttributeInfo(
#                 name="metadata.source",
#                 description="파일명-배출증관련: /mnt/배출증 출력.pdf",
#                 type="string",
#             ),
#         ]
#         return SelfQueryRetriever.from_llm(
#             llm=kwargs.get("llm", "studio"),
#             vectorstore=qdrant.get_vectorstore(),
#             # document_content_description="Skia/PDF m128",
#             document_contents="배출증 사용 매뉴얼",
#             verbose=True,
#             metadata_field_info=metadata_field_info,
#             search_kwargs={"k": top_k},
#         )
#     else:
#         raise ValueError(f"Unknown retriever name: {retriever_name}")
