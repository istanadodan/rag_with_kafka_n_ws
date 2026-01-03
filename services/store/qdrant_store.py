from services.store import qdrant_vdb
from core.config import settings


def get_qdrant_vectorstore():
    from langchain_qdrant import QdrantVectorStore
    from services.llm.embedding import embedding

    doc_store = QdrantVectorStore(
        client=qdrant_vdb.get_qdrant_client().client,
        collection_name=settings.qdrant_collection,
        embedding=embedding,
    )
    return doc_store
