from schemas.base import BaseModel, AppBaseModel
from typing import Optional
from pydantic import Field


class User(AppBaseModel):
    id: Optional[str]
    name: Optional[str]
    email: Optional[str]
    is_active: bool = Field(
        default=True,
        description="User is active or not",
    )
