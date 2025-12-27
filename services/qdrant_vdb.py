from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class QdrantClientProvider:

    def __init__(
        self,
        url: str,
        port: int,
        api_key: str,
        embedding_model_name: str,
        lazy_load: bool,
    ):
        logger.info(f"Connecting to Qdrant at {url}:{port}, key: {api_key}")
        self._client = QdrantClient(url=url, port=port, api_key=api_key)

        self._client.set_model(
            embedding_model_name=embedding_model_name,
            lazy_load=lazy_load,
            # cuda=True,
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


def get_qdrant_client() -> QdrantClientProvider:
    qdrant = QdrantClientProvider(
        url=settings.qdrant_url,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
        embedding_model_name="sentence-transformers/all-minilm-l6-v2",
        lazy_load=False,
    )

    qdrant.ensure_collection(settings.qdrant_collection, settings.embedding_dim)
    return qdrant
