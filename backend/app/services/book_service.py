"""图书发布、编辑、下架、审核、删除。

PENDING(待审核) --管理员通过--> AVAILABLE(待漂流) --同意借阅--> BORROWED(已借出) --确认归还--> AVAILABLE
PENDING --管理员驳回--> OFF_SHELF(已下架)
PENDING / AVAILABLE --发布人下架--> OFF_SHELF
PENDING / AVAILABLE / OFF_SHELF --发布人编辑--> PENDING（重新审核，防止过审后改成违规内容）
BORROWED 状态不能编辑、不能下架；管理员删除为软删除。
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.pagination import paginate
from app.core.response import BizError
from app.models import Book, BookStatus, Category, Role, User
from app.schemas import BookIn
from app.services.borrow_service import cancel_pending_borrows

PUBLIC_STATUSES = (BookStatus.AVAILABLE, BookStatus.BORROWED)


def get_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None or book.is_deleted:
        raise BizError("图书不存在", 404)
    return book


def get_visible_book(db: Session, book_id: int, user: User | None) -> Book:
    """待漂流 / 已借出的书公开可见；待审核 / 已下架的书只有发布人和管理员能看。"""
    book = get_book(db, book_id)
    if book.status in PUBLIC_STATUSES:
        return book
    if user is not None and (user.id == book.owner_id or user.role == Role.ADMIN):
        return book
    raise BizError("图书不存在", 404)


def _get_own_book(db: Session, user: User, book_id: int) -> Book:
    book = get_book(db, book_id)
    if book.owner_id != user.id:
        raise BizError("无权操作他人发布的图书", 403)
    return book


def _ensure_category(db: Session, category_id: int) -> None:
    if db.get(Category, category_id) is None:
        raise BizError("图书分类不存在")


def create_book(db: Session, user: User, data: BookIn) -> Book:
    _ensure_category(db, data.category_id)
    book = Book(**data.model_dump(), owner_id=user.id, status=BookStatus.PENDING)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, user: User, book_id: int, data: BookIn) -> Book:
    book = _get_own_book(db, user, book_id)
    if book.status == BookStatus.BORROWED:
        raise BizError("图书已借出，归还后才能编辑")
    _ensure_category(db, data.category_id)
    for field, value in data.model_dump().items():
        setattr(book, field, value)
    book.status = BookStatus.PENDING
    book.review_note = ""
    cancel_pending_borrows(db, book.id)
    db.commit()
    db.refresh(book)
    return book


def off_shelf(db: Session, user: User, book_id: int) -> Book:
    book = _get_own_book(db, user, book_id)
    if book.status == BookStatus.BORROWED:
        raise BizError("图书已借出，归还后才能下架")
    if book.status == BookStatus.OFF_SHELF:
        raise BizError("图书已经是下架状态")
    book.status = BookStatus.OFF_SHELF
    cancel_pending_borrows(db, book.id)
    db.commit()
    db.refresh(book)
    return book


def review_book(db: Session, book_id: int, approved: bool, note: str = "") -> Book:
    book = get_book(db, book_id)
    if book.status != BookStatus.PENDING:
        raise BizError("该图书不是待审核状态")
    if approved:
        book.status = BookStatus.AVAILABLE
        book.review_note = ""
    else:
        book.status = BookStatus.OFF_SHELF
        book.review_note = note or "审核未通过"
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> None:
    # 软删除：保留借还历史；已借出的书仍可以走完归还流程
    book = get_book(db, book_id)
    book.is_deleted = True
    cancel_pending_borrows(db, book.id)
    db.commit()


def _keyword_condition(keyword: str):
    return or_(Book.title.contains(keyword, autoescape=True), Book.author.contains(keyword, autoescape=True))


def list_public(db: Session, keyword: str, category_id: int | None, page: int, size: int) -> dict:
    conditions = [Book.is_deleted.is_(False), Book.status == BookStatus.AVAILABLE]
    if keyword:
        conditions.append(_keyword_condition(keyword))
    if category_id:
        conditions.append(Book.category_id == category_id)
    return paginate(db, Book, conditions, [Book.id.desc()], page, size)


def list_by_owner(db: Session, user: User, status: str | None, page: int, size: int) -> dict:
    conditions = [Book.is_deleted.is_(False), Book.owner_id == user.id]
    if status:
        conditions.append(Book.status == status)
    return paginate(db, Book, conditions, [Book.id.desc()], page, size)


def list_for_admin(db: Session, status: str | None, keyword: str, page: int, size: int) -> dict:
    conditions = [Book.is_deleted.is_(False)]
    if status:
        conditions.append(Book.status == status)
    if keyword:
        conditions.append(_keyword_condition(keyword))
    return paginate(db, Book, conditions, [Book.id.desc()], page, size)
