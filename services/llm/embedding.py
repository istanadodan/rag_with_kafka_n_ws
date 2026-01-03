from typing import Iterable, Optional, Union, Any, Protocol, List
from openai import OpenAI, APIConnectionError
import logging
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):

    def embed(self, documents: Iterable[str]) -> list[list[float]]: ...


class DummyNomicEmbedding(EmbeddingProvider, Embeddings):
    """
    요구사항: nomic 2048 차원.
    초기 버전은 더미(0벡터)로 두고, 추후 실제 임베딩으로 교체.
    """

    def __init__(self, dim: int = 2048):
        self.dim = dim

    def embed(self, documents: Iterable[str]) -> list[list[float]]:
        zero = [0.0] * self.dim
        return [zero for _ in documents]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)

    def embed_query(self, text: str) -> list[float]:
        _r = self.embed_documents([text])
        return _r[0] if len(_r) > 0 else []


class StudioLmEmbedding(EmbeddingProvider, Embeddings):
    """
    요구사항: nomic 2048 차원.
    초기 버전은 더미(0벡터)로 두고, 추후 실제 임베딩으로 교체.
    """

    def __init__(
        self, dim: int = 768, model: str = "nomic-ai/nomic-embed-text-v1.5-GGUF"
    ):
        self.client = OpenAI(
            base_url="http://host.docker.internal:11434/v1", api_key="lm-studio"
        )
        self.embed_model = model
        self.dim = dim

    def embed(self, documents: Iterable[str]) -> list[list[float]]:
        # def embed(self, texts: List[str]) -> List[List[float]]:
        # StudioLM에 API를 호출하여 texts를 임베딩데이터로 변환
        try:
            return [
                self.client.embeddings.create(
                    input=[text.replace("\n", " ")], model=self.embed_model
                )
                .data[0]
                .embedding
                for text in documents
            ]

        except APIConnectionError as e:
            logger.error(f"Embeddings failed: {str(e)}")
            raise RuntimeError("Embedding service is unavailable")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)

    def embed_query(self, text: str) -> list[float]:
        _r = self.embed_documents([text])
        return _r[0] if len(_r) > 0 else []


embedding = StudioLmEmbedding()
