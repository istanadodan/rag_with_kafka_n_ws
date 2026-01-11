from uuid import uuid4
from core.config import settings
from services.dto.rag import RagPipelineResult
from schemas.source import SourceDocument
from services.llm.embedding import EmbeddingProvider
from services.vdb.qdrant_client import QdrantClientProvider
from qdrant_client.http import models as qm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RagIngestService:
    def __init__(
        self,
        qdrant: QdrantClientProvider,
        embedder: EmbeddingProvider,
        collection: str,
    ):
        self.qdrant = qdrant
        self.embedder = embedder
        self.collection = collection

    def ingest_stub(self, file_name: str) -> RagPipelineResult | None:
        from services.vdb.qdrant_store import get_qdrant_vectorstore
        from langchain_community.document_loaders import PyPDFLoader

        # load file with the file_name
        file_path = Path("/mnt") / (file_name + ".pdf")
        logger.info("file_path=%s", file_path)
        if file_path.exists() is False:
            logger.error("File not found: %s", file_path)
            # raise FileNotFoundError(f"File not found: {file_path}")
            return

        vectors = []
        try:
            loader = PyPDFLoader(file_path)
            docs: list[Document] = loader.load()

            # extract text chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
            )

            split_docs = splitter.split_documents(docs)
            logger.info("docs doc_len=%d, spl_doc_len=%d", len(docs), len(split_docs))

            store = get_qdrant_vectorstore()
            store.add_documents(split_docs)

            # src_docs: list[SourceDocument] = [
            #     SourceDocument(page_content=d.page_content, metadata=d.metadata)
            #     for d in splitter.split_documents(docs)
            # ]
            # logger.info("docs doc_len=%d, spl_doc_len=%d", len(docs), len(src_docs))
            # vectors = self.embedder.embed([doc.page_content for doc in src_docs])

            # logger.info("vectors len=%d", len(vectors))
            # for vector, doc in zip(vectors, src_docs):
            #     logger.info("doc: %s", doc)

            #     self.qdrant.client.upsert(
            #         collection_name=self.collection,
            #         points=[
            #             qm.PointStruct(
            #                 id=str(uuid4()),
            #                 vector=vector,
            #                 payload={
            #                     "page_content": doc.page_content,
            #                     **doc.metadata,
            #                 },
            #             )
            #         ],
            #     )

        except Exception as e:
            logger.error("Ingestion failed: %s", str(e))
            return

        return RagPipelineResult(
            ingested_chunks=len(vectors),
            pdf_count=1,
        )
