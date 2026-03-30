from app.core.security import hash_password
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.utils.enums import UserRole


def run():
    db = SessionLocal()
    try:
        existing = UserRepository.get_by_email(db, "admin@flowqueue.com")
        if existing:
            print("Admin user already exists")
            return

        user = UserRepository.create_user(
            db=db,
            email="admin@flowqueue.com",
            hashed_password=hash_password("Admin123!"),
            full_name="FlowQueue Admin",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        print(f"Admin created: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    run()