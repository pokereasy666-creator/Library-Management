from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.core.pagination import paginate
from app.core.response import BizError, ok
from app.database import get_db
from app.models import Book, BookStatus, BorrowStatus, Category, ReturnStatus, Role, User
from app.schemas import (
    BookOut,
    BorrowOut,
    CategoryIn,
    CategoryOut,
    RejectIn,
    ReturnOut,
    UserOut,
    UserStatusIn,
    page_of,
)
from app.services import book_service, borrow_service

router = APIRouter(prefix="/admin", tags=["管理员"], dependencies=[Depends(require_admin)])


# ---------- 用户管理 ----------
@router.get("/users")
def list_users(
    keyword: str = Query("", max_length=32),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    conditions = []
    keyword = keyword.strip()
    if keyword:
        conditions.append(
            or_(User.username.contains(keyword, autoescape=True), User.nickname.contains(keyword, autoescape=True))
        )
    return ok(page_of(paginate(db, User, conditions, [User.id], page, size), UserOut))


@router.put("/users/{user_id}/status")
def change_user_status(user_id: int, data: UserStatusIn, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise BizError("用户不存在", 404)
    if user.role == Role.ADMIN:
        raise BizError("不能修改管理员账号的状态")
    user.status = data.status
    db.commit()
    return ok(UserOut.model_validate(user), "已禁用该用户" if data.status == "DISABLED" else "已启用该用户")


# ---------- 图书审核 ----------
@router.get("/books")
def list_books(
    status: BookStatus | None = None,
    keyword: str = Query("", max_length=50),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ok(page_of(book_service.list_for_admin(db, status, keyword.strip(), page, size), BookOut))


@router.post("/books/{book_id}/approve")
def approve_book(book_id: int, db: Session = Depends(get_db)):
    book = book_service.review_book(db, book_id, approved=True)
    return ok(BookOut.model_validate(book), "审核通过，图书已上架")


@router.post("/books/{book_id}/reject")
def reject_book(book_id: int, data: RejectIn, db: Session = Depends(get_db)):
    book = book_service.review_book(db, book_id, approved=False, note=data.note)
    return ok(BookOut.model_validate(book), "已驳回，图书变为已下架")


@router.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book_service.delete_book(db, book_id)
    return ok(None, "图书已删除")


# ---------- 分类管理 ----------
def _ensure_unique_name(db: Session, name: str, exclude_id: int | None = None) -> None:
    stmt = select(Category.id).where(Category.name == name)
    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise BizError("分类名称已存在")


@router.post("/categories")
def create_category(data: CategoryIn, db: Session = Depends(get_db)):
    _ensure_unique_name(db, data.name)
    category = Category(name=data.name)
    db.add(category)
    db.commit()
    return ok(CategoryOut.model_validate(category), "分类已新增")


@router.put("/categories/{category_id}")
def update_category(category_id: int, data: CategoryIn, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise BizError("分类不存在", 404)
    _ensure_unique_name(db, data.name, exclude_id=category_id)
    category.name = data.name
    db.commit()
    return ok(CategoryOut.model_validate(category), "分类已修改")


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise BizError("分类不存在", 404)
    # 软删除的图书也算在内：它们的借还历史仍引用这个分类
    if db.scalar(select(Book.id).where(Book.category_id == category_id).limit(1)) is not None:
        raise BizError("该分类下存在图书，无法删除")
    db.delete(category)
    db.commit()
    return ok(None, "分类已删除")


# ---------- 借还记录 ----------
@router.get("/borrows")
def list_borrows(
    status: BorrowStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ok(page_of(borrow_service.list_borrows(db, page, size, status), BorrowOut))


@router.get("/returns")
def list_returns(
    status: ReturnStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ok(page_of(borrow_service.list_returns(db, page, size, status), ReturnOut))
