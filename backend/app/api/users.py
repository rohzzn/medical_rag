from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_db_user
from app.db.session import get_db
from app.db import crud, models
from app.schemas.user import User

router = APIRouter()


@router.get("/me", response_model=User)
def read_current_user(
    current_user: models.User = Depends(get_db_user)
):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=User)
def update_current_user(
    user_update: User,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_db_user)
):
    """Update current user information."""
    # Check if email already exists
    if user_update.email != current_user.email:
        db_user = crud.get_user_by_email(db, email=user_update.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Update user
    current_user.email = user_update.email
    current_user.full_name = user_update.full_name
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user