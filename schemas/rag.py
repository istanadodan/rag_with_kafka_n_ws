from typing import List, Dict, Any
from schemas.base import AppBaseModel, MetaResponse
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
    filter: dict[str, str] = Field(
        default_factory=dict,
        examples=[{"producer": "ESP Ghostscript 7.07"}],
    )


class RagHit(AppBaseModel):
    score: float
    source: str
    metadata: Dict[str, Any]


class QueryByRagResult(AppBaseModel):
    answer: str
    hits: List[RagHit]
    model_config = {"extra": "ignore"}


class QueryByRagResponse(MetaResponse):
    result: QueryByRagResult
