from core.db.rdb import Base
from sqlalchemy import String, Integer, DateTime, Boolean, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB


class ParentDocument(Base):
    __tablename__ = "parent_document"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(nullable=False)
    mdata: Mapped[dict] = mapped_column(JSONB, nullable=False)
