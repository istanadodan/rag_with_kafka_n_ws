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
