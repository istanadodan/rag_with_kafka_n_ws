from core.db import vdb
from core.config import settings
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse
from services.llm.embedding import embedding


def get_vectorstore():

    doc_store = QdrantVectorStore(
        client=vdb.get_qdrant_client().client,
        collection_name=settings.qdrant_collection,
        embedding=embedding,
        sparse_embedding=FastEmbedSparse(),
        # vector_name="dense",
    )
    return doc_store
