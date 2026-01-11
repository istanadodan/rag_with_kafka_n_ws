from services.vdb import qdrant_client
from core.config import settings


def get_qdrant_vectorstore():
    from langchain_qdrant import QdrantVectorStore, FastEmbedSparse
    from services.llm.embedding import embedding

    doc_store = QdrantVectorStore(
        client=qdrant_client.get_qdrant_client().client,
        collection_name=settings.qdrant_collection,
        embedding=embedding,
        sparse_embedding=FastEmbedSparse(),
        # vector_name="dense",
    )
    return doc_store
