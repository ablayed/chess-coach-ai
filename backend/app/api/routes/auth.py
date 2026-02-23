from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.models.database import User
from app.models.schemas import AuthResponse, LoginRequest, RegisterRequest, UserPublic
from app.services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    existing = await db.execute(
        select(User).where(or_(User.email == request.email, User.username == request.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already in use")

    user = User(
        email=request.email,
        username=request.username,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id))
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserPublic(id=str(user.id), username=user.username, email=user.email),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user.id))
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserPublic(id=str(user.id), username=user.username, email=user.email),
    )
