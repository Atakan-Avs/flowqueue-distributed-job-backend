from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = UserRepository.get_by_email(db, email)
        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict | None:
        user = AuthService.authenticate_user(db, email, password)
        if not user:
            return None

        token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }