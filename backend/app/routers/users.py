from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import ok
from app.database import get_db
from app.models import BookStatus, User
from app.schemas import BookOut, UserOut, page_of
from app.services import book_service

router = APIRouter(prefix="/users", tags=["个人中心"])


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))


@router.get("/me/books")
def my_books(
    status: BookStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(page_of(book_service.list_by_owner(db, user, status, page, size), BookOut))
