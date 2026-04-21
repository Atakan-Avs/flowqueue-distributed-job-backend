from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    def create(db: Session, *, user_id, token_hash: str, expires_at):
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
        return db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

    @staticmethod
    def revoke(db: Session, token: RefreshToken):
        token.revoked_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def rotate(
        db: Session,
        old_token: RefreshToken,
        new_token_hash: str,
    ):
        now = datetime.now(timezone.utc)
        old_token.rotated_at = now
        old_token.revoked_at = now
        old_token.replaced_by_token_hash = new_token_hash
        db.commit()

    @staticmethod
    def revoke_all_for_user(db: Session, user_id):
        tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        ).all()

        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now

        db.commit()