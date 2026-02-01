from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.dto.rag import QueryByRagResult, RagHit
from core.db.vdb import QdrantClientProvider
from services.llm.embedding import EmbeddingProvider
from utils.logging import logging, log_block_ctx
from core.config import settings
from typing import cast
from services.llm.llm_provider import select_llm
import os

logger = logging.getLogger(__name__)

# os.environ["OPENAI_API_KEY"] = settings.openai_api_key


class AgentService:
    def __init__(
        self,
    ):
        self.llm = select_llm(settings.llm_model_name)

    # llm_model설정
    def llm_model(self, model_name: str):
        self.llm = select_llm(model_name)

    def chat(
        self,
        query: str,
        llm_model: str = "studio",
    ) -> QueryByRagResult:
        # 프롬프트 생성
        from services.agents.collector_agent import (
            DataCollectorAgent,
            StateGraphInterface,
        )

        agent: StateGraphInterface = DataCollectorAgent(llm_model)
        r = agent.run(
            data_sources=[
                {
                    "name": "계약서",
                    "source_type": "file",
                    "path": f"{query}",
                }
            ]
        )

        return QueryByRagResult(answer=str(r), hits=[])
