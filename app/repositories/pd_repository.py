from sqlalchemy.ext.asyncio import AsyncSession
from models.parent_documents import ParentDocument
from schemas.source import ParentDocumentDto
from sqlalchemy import select, Sequence
from langchain_core.documents import Document
import ast
import json


class ParentDocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, username: str, email: str) -> ParentDocument:
        user = ParentDocument(username=username, email=email)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def add_all(self, docs: list[Document]) -> list[Document]:

        models = [
            ParentDocument(
                content=doc.page_content,
                mdata=doc.metadata,
            )
            for doc in docs
        ]
        self.db.add_all(models)
        await self.db.flush()
        for m in models:
            await self.db.refresh(m)

        return [
            Document(
                page_content=d.content,
                metadata={**d.mdata, "parent_id": d.id},
                # metadata={**ast.literal_eval(d.mdata), "parent_id": d.id},
            )
            for d in models
        ]

    async def get_by_id(self, user_id: int) -> ParentDocument | None:
        result = await self.db.execute(
            select(ParentDocument).where(ParentDocument.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ParentDocumentDto]:
        result = await self.db.execute(select(ParentDocument).offset(skip).limit(limit))
        models = result.scalars()

        # Model → DTO 변환
        return [ParentDocumentDto.model_validate(model) for model in models]

    async def update(self, user: ParentDocument) -> ParentDocument:
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: ParentDocument) -> None:
        await self.db.delete(user)
