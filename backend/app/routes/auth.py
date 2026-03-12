"""Authentication routes: register, login, refresh, me."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserResponse

router = APIRouter(tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    """Create a JWT token with given claims.

    Args:
        user_id: User ID to encode as subject.
        token_type: Token type ('access' or 'refresh').
        expires_delta: Token expiration duration.

    Returns:
        Encoded JWT string.
    """
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account.

    Args:
        data: User registration data.
        db: Database session.

    Returns:
        Created user profile.

    Raises:
        HTTPException: 422 if email already exists.
    """
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=422, detail="Email already registered")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        phone=data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens.

    Args:
        data: Login credentials.
        db: Database session.

    Returns:
        Access and refresh tokens.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = _create_token(user.id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = _create_token(user.id, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh an access token using a valid refresh token.

    Args:
        data: Refresh token request.
        db: Database session.

    Returns:
        New access token.

    Raises:
        HTTPException: 401 if refresh token is invalid or expired.
    """
    try:
        payload = jwt.decode(data.refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = _create_token(user.id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user.

    Args:
        current_user: Authenticated user from JWT.

    Returns:
        User profile data.
    """
    return current_user
