from services.dto.rag import QueryByRagResult, RagHit
from services.llm.embedding import EmbeddingProvider
from utils.logging import logging, log_block_ctx, log_execution_block
from core.config import settings
from typing import cast
import os
from core.db.rdb import AsyncSession
from schemas.user import User
from repositories.user import UserRepository

logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = settings.openai_api_key


class UserService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.db = session
        self.repo = UserRepository(session)

    async def register(self, user: User) -> User:
        # 사용자 등록
        return user

    @log_execution_block(title="get_users")
    async def get_users(self) -> list[User]:
        return await self.repo.get_users()
