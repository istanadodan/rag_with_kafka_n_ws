from fastapi import APIRouter, Depends, Body
from api.schema import AgentResponse, AgentRequest
from core.middleware.trace_id import get_trace_id
from services.agent_service import AgentService

router = APIRouter()


@router.post("/")
async def agent(input: AgentRequest, trace_id: str = Depends(get_trace_id)):
    svc = AgentService()
    r = svc.chat(query=input.query)
    return AgentResponse(trace_id=trace_id, result={"message": r})
