from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_password
from app.models import Category, Role, User

DEFAULT_CATEGORIES = ("文学小说", "历史传记", "科学技术", "经济管理", "教材教辅", "其他")


def seed(db: Session) -> None:
    if db.scalar(select(User.id).where(User.username == settings.admin_username)) is None:
        db.add(
            User(
                username=settings.admin_username,
                nickname="管理员",
                password_hash=hash_password(settings.admin_password),
                role=Role.ADMIN,
            )
        )
    if db.scalar(select(func.count()).select_from(Category)) == 0:
        db.add_all(Category(name=name) for name in DEFAULT_CATEGORIES)
    db.commit()
