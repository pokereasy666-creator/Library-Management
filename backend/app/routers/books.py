from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_optional_user
from app.core.response import ok
from app.database import get_db
from app.models import User
from app.schemas import BookIn, BookOut, page_of
from app.services import book_service

router = APIRouter(prefix="/books", tags=["图书"])


@router.get("")
def list_books(
    keyword: str = Query("", max_length=50),
    category_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = book_service.list_public(db, keyword.strip(), category_id, page, size)
    return ok(page_of(result, BookOut))


@router.get("/{book_id}")
def book_detail(book_id: int, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    return ok(BookOut.model_validate(book_service.get_visible_book(db, book_id, user)))


@router.post("")
def publish_book(data: BookIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = book_service.create_book(db, user, data)
    return ok(BookOut.model_validate(book), "发布成功，等待管理员审核")


@router.put("/{book_id}")
def edit_book(book_id: int, data: BookIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = book_service.update_book(db, user, book_id, data)
    return ok(BookOut.model_validate(book), "修改成功，等待管理员重新审核")


@router.post("/{book_id}/off-shelf")
def off_shelf(book_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = book_service.off_shelf(db, user, book_id)
    return ok(BookOut.model_validate(book), "图书已下架")
