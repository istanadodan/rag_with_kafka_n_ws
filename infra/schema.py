from pydantic import BaseModel, Field
from typing import Any, Dict, Protocol


# handler 인터페이스
class BaseHandler(Protocol):

    def handle(self, message: dict) -> None: ...


class StompFrameModel(BaseModel):
    command: str = Field(..., description="The STOMP command of the frame")
    headers: Dict[str, Any] = Field(
        default_factory=dict, description="Headers of the STOMP frame"
    )
    body: str = Field("", description="Body content of the STOMP frame")


# kafka ws.in payload
class InboundMessage(BaseModel):
    destination: str
    body: str


# Kafka ws.out payload
class OutboundMessage(BaseModel):
    destination: str
    body: str
