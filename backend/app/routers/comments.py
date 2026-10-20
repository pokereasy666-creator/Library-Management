from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_optional_user
from app.core.response import ok
from app.database import get_db
from app.models import Comment, User
from app.schemas import CommentIn, CommentOut
from app.services import book_service

router = APIRouter(prefix="/books/{book_id}/comments", tags=["评论"])


@router.get("")
def list_comments(book_id: int, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    book_service.get_visible_book(db, book_id, user)
    comments = db.scalars(select(Comment).where(Comment.book_id == book_id).order_by(Comment.id)).all()
    return ok([CommentOut.model_validate(c) for c in comments])


@router.post("")
def add_comment(
    book_id: int, data: CommentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    book_service.get_visible_book(db, book_id, user)
    comment = Comment(book_id=book_id, user_id=user.id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return ok(CommentOut.model_validate(comment), "评论成功")
