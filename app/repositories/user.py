from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Sequence
from langchain_core.documents import Document
from schemas.user import User
from models.user import UserEntity


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(UserEntity).where(UserEntity.id == user_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        # Model → DTO 변환
        return User.model_validate(model)

    async def get_users(self) -> list[User]:
        result = await self.db.execute(select(UserEntity))
        models = result.scalars().all()
        # Model → DTO 변환
        return [User.model_validate(model) for model in models]
