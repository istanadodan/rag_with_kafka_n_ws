from uuid import uuid4
from schemas.rag import RagPipelineResult
from schemas.source import SourceDocument
from services.embedding import EmbeddingProvider
from services.qdrant_vdb import QdrantClientProvider
from qdrant_client.http import models as qm
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
        # load file with the file_name
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from pathlib import Path

        file_path = Path("/mnt") / (file_name + ".pdf")
        logger.info("file_path=%s", file_path)
        if file_path.exists() is False:
            raise FileNotFoundError(f"File not found: {file_path}")

        vectors = []
        try:
            loader = PyPDFLoader(file_path)
            docs: list[Document] = loader.load()
            # extract text chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=100
            )
            src_docs: list[SourceDocument] = [
                SourceDocument(page_content=d.page_content, metadata=d.metadata)
                for d in splitter.split_documents(docs)
            ]

            vectors = self.embedder.embed([doc.page_content for doc in src_docs])

            for vector, doc in zip(vectors, src_docs):
                logger.info("doc: %s", doc)

                self.qdrant.client.upsert(
                    collection_name=self.collection,
                    points=[
                        qm.PointStruct(
                            id=str(uuid4()),
                            vector=vector,
                            payload={
                                "page_content": doc.page_content,
                                **doc.metadata,
                            },
                        )
                    ],
                )

        except Exception as e:
            logger.error("Ingestion failed: %s", str(e))
            return None

        return RagPipelineResult(
            ingested_chunks=len(vectors),
            pdf_count=1,
        )
