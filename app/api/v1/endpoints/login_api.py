from fastapi import APIRouter, Depends
from schemas.api.user import (
    SignUpRequest,
    SignUpResponse,
    UserResponse,
    SignInRequest,
)
from api.deps import get_current_user, find_trace_id, get_user_service
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from supabase_auth.types import AuthResponse
from fastapi import HTTPException
from schemas.user import User
from supabase import Client, create_async_client, AClient
from utils.logging import log_block_ctx, get_logger, log_execution_block

logger = get_logger(__name__)


async def get_supabase() -> AClient:
    return await create_async_client(
        "http://supabase-kong.rag:8000",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsaG9zdCIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjQxNzY5MjAwLCJleHAiOjE5NTczNDUyMDB9.nsv6ak_BFsjGN9cQ3BzYN35ZExCLgXF8E7O1tx55MSs",
    )


router = APIRouter()


@router.post("/login")
async def login_for_access_token(
    # form_data: OAuth2PasswordRequestForm = Depends(),
    user_input: SignInRequest,
    supabase: AClient = Depends(get_supabase),
):
    """
    로그인이 성공하면 접근토큰과 갱신토큰을 반환

    :param form_data: Description
    :type form_data: OAuth2PasswordRequestForm
    :param supabase: Description
    :type supabase: AClient
    """
    res: AuthResponse = await supabase.auth.sign_in_with_password(
        {"email": user_input.email, "password": user_input.password}
    )

    if not res or not res.session:
        raise HTTPException(status_code=401, detail="Bad credentials")

    return {
        "token_type": "bearer",
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
    }


@router.post("/signup", response_model=SignUpResponse)
@log_execution_block(title="API:signup")
async def signup(
    input: SignUpRequest,
    supabase: AClient = Depends(get_supabase),
    trace_id=Depends(find_trace_id),
):
    res: AuthResponse = await supabase.auth.sign_up(
        {"email": input.email, "password": input.password}
    )

    if not res.session:
        raise HTTPException(status_code=400, detail="Signup failed")

    return SignUpResponse(
        user=User(
            id=getattr(res.user, "id"),
            email=getattr(res.user, "email"),
            name=input.name,
        ),
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        trace_id=trace_id,
    )


from core.security import check_security
from api.deps import get_db
from services.user_service import UserService


@router.get("/users", response_model=UserResponse)
async def protected(
    trace_id: str = Depends(find_trace_id),
    session=Depends(get_db),
    security=Depends(check_security),
):
    svc = UserService(session)
    users: list[User] = await svc.get_users()
    return UserResponse(trace_id=trace_id, users=await svc.get_users())


# @router.post("/users", response_model=UserResponse, status_code=201)
# async def create_user(
#     user_data: UserCreate, db: AsyncSession = Depends(get_async_session)
# ):
#     """새 사용자 생성"""
#     # 이메일 중복 체크
#     result = await db.execute(select(User).where(User.email == user_data.email))
#     existing_user = result.scalar_one_or_none()

#     if existing_user:
#         raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

#     # 새 사용자 생성
#     new_user = User(name=user_data.name, email=user_data.email)
#     db.add(new_user)
#     await db.flush()  # ID를 즉시 얻기 위해
#     await db.refresh(new_user)  # 객체 새로고침

#     return new_user


# @router.get("/users", response_model=list[UserResponse])
# async def get_users(
#     skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)
# ):
#     """사용자 목록 조회"""
#     result = await db.execute(select(User).offset(skip).limit(limit))
#     users = result.scalars().all()
#     return users


# @router.get("/users/{user_id}", response_model=UserResponse)
# async def get_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
#     """특정 사용자 조회"""
#     result = await db.execute(select(User).where(User.id == user_id))
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

#     return user


# @router.put("/users/{user_id}", response_model=UserResponse)
# async def update_user(
#     user_id: int, user_data: UserCreate, db: AsyncSession = Depends(get_async_session)
# ):
#     """사용자 정보 업데이트"""
#     result = await db.execute(select(User).where(User.id == user_id))
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

#     # 이메일 중복 체크 (자기 자신 제외)
#     email_result = await db.execute(
#         select(User).where(User.email == user_data.email, User.id != user_id)
#     )
#     if email_result.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

#     # 업데이트
#     user.name = user_data.name
#     user.email = user_data.email
#     await db.flush()
#     await db.refresh(user)

#     return user


# @router.delete("/users/{user_id}", status_code=204)
# async def delete_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
#     """사용자 삭제"""
#     result = await db.execute(select(User).where(User.id == user_id))
#     user = result.scalar_one_or_none()

#     if not user:
#         raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

#     await db.delete(user)
#     return None
