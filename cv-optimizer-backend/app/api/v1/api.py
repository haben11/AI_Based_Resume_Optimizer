from fastapi import APIRouter
from app.api.v1.endpoints import cv_optimizer, auth, users, structured_resume

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cv_optimizer.router, prefix="/optimize", tags=["optimizer"])
api_router.include_router(structured_resume.router, prefix="/resumes", tags=["structured-resumes"])
