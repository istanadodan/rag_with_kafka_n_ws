from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import logging

logger = logging.getLogger(__name__)


class QdrantClientProvider:
    def __init__(self, url: str, port: int, api_key: str | None):
        logger.info(f"Connecting to Qdrant at {url}:{port}, key: {api_key}")
        # self._client = QdrantClient(url=url, api_key=api_key)
        # self._client = QdrantClient(
        #     url="https://4ed5d8d6-7a02-4931-815f-69bacca195d3.europe-west3-0.gcp.cloud.qdrant.io:6333",
        #     api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY"
        #     "2Nlc3MiOiJtIn0.II_Y19M_QxoUWGqhMcjtR9eqfPkCzJUvYW50WIjxcjc",
        # )
        self._client = QdrantClient(url=url, port=port, api_key=api_key)
        self._client.set_model(
            embedding_model_name="sentence-transformers/all-minilm-l6-v2",
            # cuda=True,
            lazy_load=False,
        )

    @property
    def client(self) -> QdrantClient:
        return self._client

    def ensure_collection(self, name: str, vector_size: int) -> None:
        # 이미 존재하면 통과, 없으면 생성
        collections = self._client.get_collections().collections
        if any(c.name == name for c in collections):
            return
        # 초기화
        self._client.delete_collection(name)
        self._client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
