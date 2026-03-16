"""Routes for greenhouses."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Greenhouse, User
from app.schemas import (
    GreenhouseCreate,
    GreenhouseListResponse,
    GreenhouseResponse,
    GreenhouseUpdate,
)

router = APIRouter(tags=["greenhouses"])


@router.get("/greenhouses", response_model=GreenhouseListResponse)
def list_greenhouses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all greenhouses owned by the current user.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        Total count and list of greenhouses.
    """
    greenhouses = (
        db.query(Greenhouse)
        .filter(Greenhouse.user_id == current_user.id)
        .all()
    )
    return {"total": len(greenhouses), "greenhouses": greenhouses}


@router.get("/greenhouses/{greenhouse_id}", response_model=GreenhouseResponse)
def get_greenhouse(
    greenhouse_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single greenhouse by ID with eager-loaded devices and scripts.

    Args:
        greenhouse_id: The ID of the greenhouse to retrieve.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The greenhouse with its devices and scripts.

    Raises:
        HTTPException: 404 if not found or not owned by current user.
    """
    greenhouse = (
        db.query(Greenhouse)
        .options(joinedload(Greenhouse.devices), joinedload(Greenhouse.scripts))
        .filter(
            Greenhouse.id == greenhouse_id,
            Greenhouse.user_id == current_user.id,
        )
        .first()
    )
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Greenhouse not found",
        )
    return greenhouse


@router.post(
    "/greenhouses",
    response_model=GreenhouseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_greenhouse(
    data: GreenhouseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new greenhouse for the current user.

    Args:
        data: Greenhouse creation payload.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The newly created greenhouse.
    """
    greenhouse = Greenhouse(**data.model_dump(), user_id=current_user.id)
    db.add(greenhouse)
    db.commit()
    db.refresh(greenhouse)
    return greenhouse


@router.put("/greenhouses/{greenhouse_id}", response_model=GreenhouseResponse)
def update_greenhouse(
    greenhouse_id: int,
    data: GreenhouseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing greenhouse's name or location.

    Args:
        greenhouse_id: The ID of the greenhouse to update.
        data: Greenhouse update payload.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated greenhouse.

    Raises:
        HTTPException: 404 if not found or not owned by current user.
    """
    greenhouse = (
        db.query(Greenhouse)
        .filter(
            Greenhouse.id == greenhouse_id,
            Greenhouse.user_id == current_user.id,
        )
        .first()
    )
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Greenhouse not found",
        )
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(greenhouse, key, value)
    db.commit()
    db.refresh(greenhouse)
    return greenhouse


@router.delete(
    "/greenhouses/{greenhouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_greenhouse(
    greenhouse_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a greenhouse owned by the current user.

    Args:
        greenhouse_id: The ID of the greenhouse to delete.
        current_user: The authenticated user.
        db: Database session.

    Raises:
        HTTPException: 404 if not found or not owned by current user.
    """
    greenhouse = (
        db.query(Greenhouse)
        .filter(
            Greenhouse.id == greenhouse_id,
            Greenhouse.user_id == current_user.id,
        )
        .first()
    )
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Greenhouse not found",
        )
    db.delete(greenhouse)
    db.commit()
