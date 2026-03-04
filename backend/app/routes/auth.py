from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.dependencies import get_db
from app.schemas import TokenRefresh, TokenResponse, UserCreate, UserLogin, UserResponse
from app.services import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    register_user,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db=Depends(get_db)):
    user = register_user(db, data.model_dump())
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db=Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user["id"]),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: TokenRefresh, db=Depends(get_db)):
    payload = verify_refresh_token(data.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return TokenResponse(
        access_token=create_access_token(int(payload["sub"])),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
