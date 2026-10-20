from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class BookStatus(StrEnum):
    PENDING = "PENDING"  # 待审核
    AVAILABLE = "AVAILABLE"  # 待漂流
    BORROWED = "BORROWED"  # 已借出
    OFF_SHELF = "OFF_SHELF"  # 已下架


class BorrowStatus(StrEnum):
    PENDING = "PENDING"  # 待处理
    APPROVED = "APPROVED"  # 已同意（借阅中）
    REJECTED = "REJECTED"  # 已拒绝
    CANCELED = "CANCELED"  # 已失效：图书被借给他人、下架、重新审核或删除
    RETURNED = "RETURNED"  # 已归还


class ReturnStatus(StrEnum):
    PENDING = "PENDING"  # 待确认
    CONFIRMED = "CONFIRMED"  # 已确认归还
    REJECTED = "REJECTED"  # 拒绝归还


BOOK_CONDITIONS = ("全新", "九成新", "八成新", "七成新及以下")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10), default=Role.USER)
    status: Mapped[str] = mapped_column(String(10), default=UserStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    author: Mapped[str] = mapped_column(String(50), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    condition: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(16), default=BookStatus.PENDING, index=True)
    review_note: Mapped[str] = mapped_column(String(255), default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    owner: Mapped[User] = relationship(lazy="joined")
    category: Mapped[Category] = relationship(lazy="joined")

    @property
    def category_name(self) -> str:
        return self.category.name if self.category else ""


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped[User] = relationship(lazy="joined")


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    borrow_id: Mapped[int] = mapped_column(ForeignKey("borrow_requests.id"), index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    borrower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(16), default=ReturnStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    book: Mapped[Book] = relationship(lazy="joined")
    borrower: Mapped[User] = relationship(foreign_keys=[borrower_id], lazy="joined")
    owner: Mapped[User] = relationship(foreign_keys=[owner_id], lazy="joined")
    borrow: Mapped["BorrowRequest"] = relationship(back_populates="returns")


class BorrowRequest(Base):
    __tablename__ = "borrow_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), index=True)
    # owner_id 冗余保存图书发布人，查询"我收到的申请"时不用再关联图书表
    borrower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(16), default=BorrowStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    book: Mapped[Book] = relationship(lazy="joined")
    borrower: Mapped[User] = relationship(foreign_keys=[borrower_id], lazy="joined")
    owner: Mapped[User] = relationship(foreign_keys=[owner_id], lazy="joined")
    returns: Mapped[list[ReturnRequest]] = relationship(
        back_populates="borrow", order_by=ReturnRequest.id, lazy="selectin"
    )
