from typing import Iterable, Optional, Union, Any, Protocol, List
from openai import OpenAI, APIConnectionError
import logging
from fastembed.text.text_embedding_base import TextEmbeddingBase
from fastembed.common.types import NumpyArray

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):

    def embed(self, documents: Iterable[str]) -> list[list[float]]: ...


class DummyNomicEmbedding(EmbeddingProvider):
    """
    요구사항: nomic 2048 차원.
    초기 버전은 더미(0벡터)로 두고, 추후 실제 임베딩으로 교체.
    """

    def __init__(self, dim: int = 2048):
        self.dim = dim

    def embed(self, documents: Iterable[str]) -> list[list[float]]:
        zero = [0.0] * self.dim
        return [zero for _ in documents]


class StudioLmEmbedding(EmbeddingProvider):
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
            raise Exception("Embedding service is unavailable")


class StudioLmEmbedding1(TextEmbeddingBase):
    """
    요구사항: nomic 2048 차원.
    초기 버전은 더미(0벡터)로 두고, 추후 실제 임베딩으로 교체.
    """

    def __init__(
        self, dim: int = 768, model: str = "nomic-ai/nomic-embed-text-v1.5-GGUF"
    ):
        super().__init__(model_name=model)
        self.client = OpenAI(
            base_url="http://host.docker.internal:11434/v1", api_key="lm-studio"
        )
        self.embed_model = model
        self.dim = dim

    def embed(
        self,
        documents: Union[str, Iterable[str]],
        batch_size: int = 256,
        parallel: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterable[NumpyArray]:
        import numpy as np

        # def embed(self, texts: List[str]) -> List[List[float]]:
        # StudioLM에 API를 호출하여 texts를 임베딩데이터로 변환
        try:
            return np.array(
                [
                    self.client.embeddings.create(
                        input=[text.replace("\n", " ")], model=self.embed_model
                    )
                    .data[0]
                    .embedding
                    for text in documents
                ]
            )
        except APIConnectionError as e:
            logger.error(f"Embeddings failed: {str(e)}")
            raise Exception("Embedding service is unavailable")

    @property
    def embedding_size(self) -> int:
        return self.dim
