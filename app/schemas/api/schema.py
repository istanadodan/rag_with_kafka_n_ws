from typing import List, Dict, Any, Optional
from schemas.base import AppBaseModel, MetaResponse
from pydantic import Field
from services.dto.rag import RagHit


class RagPipelineResponse(MetaResponse):
    result: str = Field(default="OK")


class QueryByRagRequest(AppBaseModel):
    query: str
    top_k: int = 3
    llm: str = ""
    retriever: str = "qdrant"
    filter: dict[str, str] = Field(
        default_factory=dict,
        examples=[{"producer": "ESP Ghostscript 7.07"}],
    )


from datetime import datetime


class QueryByRagResponse(MetaResponse):
    result: str = Field(default="OK")


class AgentRequest(AppBaseModel):
    query: str
    llm: str


class AgentResponse(MetaResponse):
    result: dict = Field(default_factory=dict)
    hits: List = Field(default_factory=list)


class QueryVdbRequest(AppBaseModel):
    query: str
    filter: dict[str, str] = Field(
        default_factory=dict,
        examples=[{"metadata.producer": "Skia/PDF m128"}],
    )
    top_k: int = 3
    retriever: str = "qdrant"


class QueryVdbResponse(MetaResponse):
    result: str
    hits: List[RagHit]
    model_config = {"extra": "ignore"}
