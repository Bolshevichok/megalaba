from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.database import MockSession
from app.dependencies import get_db
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db=Depends(get_db)):
    db_status = "available"
    if not isinstance(db, MockSession):
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        except Exception:
            db_status = "unavailable"
    return HealthResponse(
        status="ok",
        db=db_status,
        timestamp=datetime.now(timezone.utc),
    )
