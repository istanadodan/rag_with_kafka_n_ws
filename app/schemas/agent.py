from schemas.base import AppBaseModel
from typing import Annotated, Sequence, Protocol
import operator
from pydantic import Field


class StateGraphInterface(Protocol):

    def run(self, data_sources: list[dict]) -> dict: ...


# langGraph 상태클래스
class CollectorState(AppBaseModel):
    data_sources: list[dict]
    current_source_index: int = Field(default=0)
    collected_data: dict = Field(default_factory=dict)
    messages: Annotated[list[str], ""] = Field(default_factory=list)
    steps_log: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class AnalyzerState(AppBaseModel):
    """분석 Agent 상태"""

    collected_data: dict = Field(description="수집된 자료")
    analysis_types: list[str] = Field(
        default=["통계"], description="통계, 트렌드, 이상치탐색"
    )
    messages: list[str] = Field(default_factory=list, description="질의 및 답변메시지")
    data_profile: dict = Field(
        description="수집된 자료에서 테이블과 텍스트 데이터를 분리; type이 tabular, text로 분류"
    )
    analysis_results: dict = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)
    current_analysis_index: int = Field(default=0)
    steps_log: list[dict] = Field(default_factory=list)
