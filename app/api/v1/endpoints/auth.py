from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    result = AuthService.login(db, payload.email, payload.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return result


@router.post("/auth/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    result = AuthService.refresh(db, payload.refresh_token)
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )
    return result


@router.post("/auth/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    success = AuthService.logout(db, payload.refresh_token)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid token",
        )
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user