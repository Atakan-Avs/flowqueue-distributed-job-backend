from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = UserRepository.get_by_email(db, email)
        if not user or not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    def login(db: Session, email: str, password: str):
        user = AuthService.authenticate_user(db, email, password)
        if not user:
            return None

        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
        )

        refresh_token = create_refresh_token(user_id=str(user.id))

        token_hash = hash_token(refresh_token)

        payload = decode_token(refresh_token)

        RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


    @staticmethod
    def refresh(db: Session, refresh_token: str):
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            return None
        
        if payload.get("type") != "refresh":
            return None
        
        token_hash = hash_token(refresh_token)
        db_token = RefreshTokenRepository.get_by_hash(db, token_hash)
        if not db_token:
            return None
        
        if db_token.revoked_at is not None:
            RefreshTokenRepository.revoke_all_for_user(db, db_token.user_id)
            return None
        
        if db_token.expires_at < datetime.now(timezone.utc):
            RefreshTokenRepository.revoke_all_for_user(db, db_token.user_id)
            return None
        
        user = UserRepository.get_by_id(db, db_token.user_id)
        if not user:
            return None
        
        new_access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
        )
        
        new_refresh_token = create_refresh_token(user_id=str(user.id))
        new_hash = hash_token(new_refresh_token)
        
        payload_new = decode_token(new_refresh_token)
        
        RefreshTokenRepository.create(
            db=db,
            user_id=user.id,
            token_hash=new_hash,
            expires_at=datetime.fromtimestamp(payload_new["exp"], tz=timezone.utc),
        )
        RefreshTokenRepository.rotate(
            db=db,
            old_token=db_token,
            new_token_hash=new_hash,
        )
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def logout(db: Session, refresh_token: str):
        token_hash = hash_token(refresh_token)
        db_token = RefreshTokenRepository.get_by_hash(db, token_hash)

        if not db_token:
            return False

        RefreshTokenRepository.revoke(db, db_token)
        return True