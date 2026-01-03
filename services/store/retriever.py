from langchain_community.retrievers.qdrant_sparse_vector_retriever import (
    QdrantSparseVectorRetriever,
)
from langchain_community.retrievers.bm25 import BM25Retriever


class RetrieverProvider:
    def __init__(self, retriever, retriever_name):
        self.retriever = retriever
        self.retriever_name = retriever_name

    def get_retriever(self):
        return self.retriever

    def get_retriever_name(self):
        return self.retriever_name


from services.store.qdrant_vdb import get_qdrant_client
from qdrant_client.http.models import VectorParams, Distance, Bm25Config


def get_retriever(retriever_name, filter: dict, top_k: int):

    if retriever_name == "qdrant":
        from services.store.qdrant_store import get_qdrant_vectorstore

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
    else:
        raise ValueError(f"Unknown retriever name: {retriever_name}")
