from fastapi import Request, Depends
from core.config import settings
from core.db import get_qdrant_client, async_session
from contextlib import asynccontextmanager
from repositories.source_repository import SourceRepository
from services.llm.embedding import embedding
from services.ingest_service import RagIngestService
from services.rag_service import RagQueryService
from utils.logging import log_block_ctx, logging
from schemas.user import User
from fastapi import HTTPException
from repositories.user import UserRepository
from jose import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)


# 의존성: FastAPI에서 DB 세션 제공
async def get_db():  # -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


@asynccontextmanager
async def db_session_ctx():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


qdrant_vdb = get_qdrant_client()
source_repo = SourceRepository()

_rag_ingest_service = RagIngestService(
    qdrant=qdrant_vdb,
    embedder=embedding,
    collection=settings.qdrant_collection,
)
_rag_query_service = RagQueryService(
    qdrant=qdrant_vdb, embedder=embedding, collection=settings.qdrant_collection
)


def find_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "APP")


# ---- Endpoint DI wiring ----
def get_ingest_service(request: Request | None = None) -> RagIngestService:
    return _rag_ingest_service


def get_rag_service(request: Request) -> RagQueryService:
    return _rag_query_service


from services.user_service import UserService


def get_user_service(request: Request, session=Depends(get_db)) -> UserService:
    return UserService(session)


# header
security = HTTPBearer()

from core.security import check_security


async def get_current_user(
    claim: dict = Depends(check_security),
    session=Depends(get_db),
) -> User | None:

    user_id = claim.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    repo = UserRepository(session)
    return await repo.get_user(user_id)
