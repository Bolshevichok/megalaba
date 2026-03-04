from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db
from app.schemas import DashboardOverview
from app.services import get_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def overview(db=Depends(get_db), _user=Depends(get_current_user)):
    return get_overview(db)
