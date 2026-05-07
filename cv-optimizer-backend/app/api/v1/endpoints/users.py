from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.crud_user import user_repo
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    if user_in.email:
        user = user_repo.get_by_email(db, email=user_in.email)
        if user and user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
    
    return user_repo.update(db, db_obj=current_user, obj_in=user_in)

@router.delete("/me", response_model=UserSchema)
def delete_user_me(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    current_user.is_active = False
    db.add(current_user)
    db.commit()
    return current_user
