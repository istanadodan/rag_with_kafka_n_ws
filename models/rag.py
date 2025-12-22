from typing import List, Dict, Any
from models.base import AppBaseModel, MetaResponse
from pydantic import Field


class RagPipelineRequest(AppBaseModel):
    force: bool = False


class RagPipelineResult(AppBaseModel):
    ingested_chunks: int
    pdf_count: int


class RagPipelineResponse(MetaResponse):
    result: str = Field(default="OK")


class QueryByRagRequest(AppBaseModel):
    query: str
    top_k: int = 5


class RagHit(AppBaseModel):
    score: float
    source: str
    metadata: Dict[str, Any]


class QueryByRagResult(AppBaseModel):
    answer: str
    hits: List[RagHit]


class QueryByRagResponse(MetaResponse):
    result: QueryByRagResult
