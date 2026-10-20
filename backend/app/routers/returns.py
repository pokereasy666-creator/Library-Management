from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import ok
from app.database import get_db
from app.models import ReturnStatus, User
from app.schemas import ReturnIn, ReturnOut, page_of
from app.services import borrow_service

router = APIRouter(prefix="/returns", tags=["归还"])


@router.post("")
def apply_return(data: ReturnIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ret = borrow_service.create_return(db, user, data)
    return ok(ReturnOut.model_validate(ret), "归还申请已提交，等待发布人确认")


@router.get("/mine")
def my_returns(
    status: ReturnStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = borrow_service.list_returns(db, page, size, status, borrower_id=user.id)
    return ok(page_of(result, ReturnOut))


@router.get("/received")
def received_returns(
    status: ReturnStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = borrow_service.list_returns(db, page, size, status, owner_id=user.id)
    return ok(page_of(result, ReturnOut))


@router.post("/{return_id}/confirm")
def confirm(return_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ret = borrow_service.confirm_return(db, user, return_id)
    return ok(ReturnOut.model_validate(ret), "已确认归还，图书重新进入待漂流")


@router.post("/{return_id}/reject")
def reject(return_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ret = borrow_service.reject_return(db, user, return_id)
    return ok(ReturnOut.model_validate(ret), "已拒绝归还，图书保持已借出")
