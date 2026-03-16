"""FastAPI dependencies for database sessions and authentication."""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

security = HTTPBearer()


def _auth_error(code: str, message: str) -> HTTPException:
    """Build a 401 HTTPException with standardized error body.

    Args:
        code: Error code string.
        message: Human-readable message.

    Returns:
        HTTPException with 401 status.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT token, return the authenticated user.

    Args:
        credentials: Bearer token from Authorization header.
        db: Database session.

    Returns:
        User: Authenticated user object.

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "access":
            raise _auth_error("INVALID_CREDENTIALS", "Invalid token")
    except JWTError:
        raise _auth_error("TOKEN_EXPIRED", "Token is invalid or expired")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise _auth_error("INVALID_CREDENTIALS", "User not found")
    return user
