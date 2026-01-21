from fastapi import APIRouter
from api.v1.endpoints import rag_api, websocket_api, health_api, agent_api

router = APIRouter()
# router.add_api_websocket_route("/ws", websocket_api.websocket_endpoint)
router.include_router(websocket_api.router, tags=["websocket"])
router.include_router(health_api.router, tags=["health check"], include_in_schema=True)
router.include_router(
    rag_api.router, prefix="/app", tags=["app"], include_in_schema=True
)
router.include_router(agent_api.router, prefix="/agent", tags=["agent"])
