from typing import List, Dict, Any, Optional
from pydantic import Field
from schemas.base import AppBaseModel, MetaResponse
from schemas.user import User


class SignUpRequest(AppBaseModel):
    name: str
    email: str
    password: str


class SignInRequest(AppBaseModel):
    email: str
    password: str


class SignUpResponse(MetaResponse):
    access_token: str
    refresh_token: str
    user: User


class UserResponse(MetaResponse):
    users: list[User] | None
