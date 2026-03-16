"""Routes for automation scripts."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Greenhouse, Script, User
from app.schemas import ScriptCreate, ScriptResponse, ScriptUpdate

router = APIRouter(tags=["scripts"])


@router.get("/greenhouses/{greenhouse_id}/scripts")
def list_scripts(
    greenhouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all automation scripts for a greenhouse.

    Args:
        greenhouse_id: ID of the greenhouse.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        Dict with a list of scripts for the greenhouse.

    Raises:
        HTTPException: 404 if greenhouse not found or not owned by user.
    """
    greenhouse = (
        db.query(Greenhouse)
        .filter(Greenhouse.id == greenhouse_id, Greenhouse.user_id == current_user.id)
        .first()
    )
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Greenhouse not found",
        )
    scripts = db.query(Script).filter(Script.greenhouse_id == greenhouse_id).all()
    return {"scripts": [ScriptResponse.model_validate(s) for s in scripts]}


@router.post(
    "/greenhouses/{greenhouse_id}/scripts",
    status_code=status.HTTP_201_CREATED,
    response_model=ScriptResponse,
)
def create_script(
    greenhouse_id: int,
    payload: ScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScriptResponse:
    """Create a new automation script for a greenhouse.

    Args:
        greenhouse_id: ID of the greenhouse.
        payload: Script creation data.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        The newly created script.

    Raises:
        HTTPException: 404 if greenhouse not found or not owned by user.
    """
    greenhouse = (
        db.query(Greenhouse)
        .filter(Greenhouse.id == greenhouse_id, Greenhouse.user_id == current_user.id)
        .first()
    )
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Greenhouse not found",
        )
    script = Script(
        greenhouse_id=greenhouse_id,
        name=payload.name,
        script_code=payload.script_code,
        enabled=payload.enabled,
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return ScriptResponse.model_validate(script)


@router.put("/scripts/{script_id}", response_model=ScriptResponse)
def update_script(
    script_id: int,
    payload: ScriptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScriptResponse:
    """Update an existing automation script.

    Args:
        script_id: ID of the script to update.
        payload: Fields to update.
        db: Database session.
        current_user: Authenticated user.

    Returns:
        The updated script.

    Raises:
        HTTPException: 404 if script not found or not owned by user.
    """
    script = (
        db.query(Script)
        .join(Greenhouse, Script.greenhouse_id == Greenhouse.id)
        .filter(Script.id == script_id, Greenhouse.user_id == current_user.id)
        .first()
    )
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found",
        )
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(script, field, value)
    db.commit()
    db.refresh(script)
    return ScriptResponse.model_validate(script)


@router.delete("/scripts/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an automation script.

    Args:
        script_id: ID of the script to delete.
        db: Database session.
        current_user: Authenticated user.

    Raises:
        HTTPException: 404 if script not found or not owned by user.
    """
    script = (
        db.query(Script)
        .join(Greenhouse, Script.greenhouse_id == Greenhouse.id)
        .filter(Script.id == script_id, Greenhouse.user_id == current_user.id)
        .first()
    )
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found",
        )
    db.delete(script)
    db.commit()
