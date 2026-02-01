from core.db.rdb import Base
from sqlalchemy import String, Integer, DateTime, Boolean, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class UserEntity(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
