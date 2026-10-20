from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import ok
from app.database import get_db
from app.models import BorrowStatus, User
from app.schemas import BorrowIn, BorrowOut, page_of
from app.services import borrow_service

router = APIRouter(prefix="/borrows", tags=["借阅"])


@router.post("")
def apply_borrow(data: BorrowIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    borrow = borrow_service.create_borrow(db, user, data)
    return ok(BorrowOut.model_validate(borrow), "借阅申请已提交，等待发布人处理")


@router.get("/mine")
def my_borrows(
    status: BorrowStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = borrow_service.list_borrows(db, page, size, status, borrower_id=user.id)
    return ok(page_of(result, BorrowOut))


@router.get("/received")
def received_borrows(
    status: BorrowStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = borrow_service.list_borrows(db, page, size, status, owner_id=user.id)
    return ok(page_of(result, BorrowOut))


@router.post("/{borrow_id}/approve")
def approve(borrow_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    borrow = borrow_service.approve_borrow(db, user, borrow_id)
    return ok(BorrowOut.model_validate(borrow), "已同意借阅，图书状态变为已借出")


@router.post("/{borrow_id}/reject")
def reject(borrow_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    borrow = borrow_service.reject_borrow(db, user, borrow_id)
    return ok(BorrowOut.model_validate(borrow), "已拒绝该借阅申请")
