from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core import security
from app.crud.crud_user import user_repo
from app.schemas.user import User as UserSchema, UserCreate
from app.schemas.token import Token
from app.schemas.msg import Msg
from app.core.logging import logger

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = user_repo.get_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=60)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserSchema)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
) -> Any:
    user = user_repo.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    return user_repo.create(db, obj_in=user_in)

@router.post("/password-recovery/{email}", response_model=Msg)
def recover_password(email: str, db: Session = Depends(get_db)) -> Any:
    user = user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = security.create_password_reset_token(email=email)
    logger.info("password_recovery_token_generated", email=email, token=password_reset_token)
    return {"msg": "Password recovery email sent (Check logs in this dev version)"}

@router.post("/reset-password/", response_model=Msg)
def reset_password(
    token: str, new_password: str, db: Session = Depends(get_db)
) -> Any:
    email = security.verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    user_repo.update(db, db_obj=user, obj_in={"password": new_password})
    return {"msg": "Password updated successfully"}
