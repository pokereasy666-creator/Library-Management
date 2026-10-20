"""借阅 / 归还状态机。

借阅申请：PENDING → APPROVED → RETURNED
                 ↘ REJECTED / CANCELED
归还申请：PENDING → CONFIRMED / REJECTED（被拒后借书人可再次提交）

状态变更都用 "UPDATE ... WHERE status = 旧状态" 的条件更新，按影响行数判断是否成功，
这样并发操作同一本书或同一条申请时只有一个能成功。
"""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.pagination import paginate
from app.core.response import BizError
from app.models import Book, BookStatus, BorrowRequest, BorrowStatus, ReturnRequest, ReturnStatus, User
from app.schemas import BorrowIn, ReturnIn


def _transition(db: Session, model, obj_id: int, expected: str, target: str, stamp: bool = True) -> bool:
    values = {"status": target}
    if stamp:
        values["handled_at"] = datetime.now()
    result = db.execute(update(model).where(model.id == obj_id, model.status == expected).values(**values))
    return result.rowcount == 1


def cancel_pending_borrows(db: Session, book_id: int, exclude_id: int | None = None) -> None:
    """图书被借给他人、下架、重新审核或删除时，让其余待处理的借阅申请失效。调用方负责提交事务。"""
    stmt = update(BorrowRequest).where(
        BorrowRequest.book_id == book_id, BorrowRequest.status == BorrowStatus.PENDING
    )
    if exclude_id is not None:
        stmt = stmt.where(BorrowRequest.id != exclude_id)
    db.execute(stmt.values(status=BorrowStatus.CANCELED, handled_at=datetime.now()))


# ---------- 借阅 ----------
def create_borrow(db: Session, user: User, data: BorrowIn) -> BorrowRequest:
    book = db.get(Book, data.book_id)
    if book is None or book.is_deleted:
        raise BizError("图书不存在", 404)
    if book.owner_id == user.id:
        raise BizError("不能借阅自己发布的图书")
    if book.status != BookStatus.AVAILABLE:
        raise BizError("该图书当前不可借阅")
    duplicate = db.scalar(
        select(BorrowRequest.id).where(
            BorrowRequest.book_id == book.id,
            BorrowRequest.borrower_id == user.id,
            BorrowRequest.status == BorrowStatus.PENDING,
        )
    )
    if duplicate is not None:
        raise BizError("你已提交过该图书的借阅申请，请等待发布人处理")
    borrow = BorrowRequest(book_id=book.id, borrower_id=user.id, owner_id=book.owner_id, message=data.message)
    db.add(borrow)
    db.commit()
    db.refresh(borrow)
    return borrow


def _get_borrow_as_owner(db: Session, user: User, borrow_id: int) -> BorrowRequest:
    borrow = db.get(BorrowRequest, borrow_id)
    if borrow is None:
        raise BizError("借阅申请不存在", 404)
    if borrow.owner_id != user.id:
        raise BizError("无权处理他人图书的借阅申请", 403)
    return borrow


def approve_borrow(db: Session, user: User, borrow_id: int) -> BorrowRequest:
    borrow = _get_borrow_as_owner(db, user, borrow_id)
    if borrow.status != BorrowStatus.PENDING:
        raise BizError("该申请已处理，请刷新后查看")
    lent = db.execute(
        update(Book)
        .where(Book.id == borrow.book_id, Book.status == BookStatus.AVAILABLE, Book.is_deleted.is_(False))
        .values(status=BookStatus.BORROWED)
    )
    if lent.rowcount != 1:
        db.rollback()
        raise BizError("图书当前不可借出，可能已借给他人或已下架")
    if not _transition(db, BorrowRequest, borrow.id, BorrowStatus.PENDING, BorrowStatus.APPROVED):
        db.rollback()
        raise BizError("该申请已处理，请刷新后查看")
    cancel_pending_borrows(db, borrow.book_id, exclude_id=borrow.id)
    db.commit()
    db.refresh(borrow)
    return borrow


def reject_borrow(db: Session, user: User, borrow_id: int) -> BorrowRequest:
    borrow = _get_borrow_as_owner(db, user, borrow_id)
    if not _transition(db, BorrowRequest, borrow.id, BorrowStatus.PENDING, BorrowStatus.REJECTED):
        raise BizError("该申请已处理，请刷新后查看")
    db.commit()
    db.refresh(borrow)
    return borrow


def list_borrows(
    db: Session,
    page: int,
    size: int,
    status: str | None = None,
    borrower_id: int | None = None,
    owner_id: int | None = None,
) -> dict:
    conditions = []
    if status:
        conditions.append(BorrowRequest.status == status)
    if borrower_id is not None:
        conditions.append(BorrowRequest.borrower_id == borrower_id)
    if owner_id is not None:
        conditions.append(BorrowRequest.owner_id == owner_id)
    return paginate(db, BorrowRequest, conditions, [BorrowRequest.id.desc()], page, size)


# ---------- 归还 ----------
def create_return(db: Session, user: User, data: ReturnIn) -> ReturnRequest:
    borrow = db.get(BorrowRequest, data.borrow_id)
    if borrow is None:
        raise BizError("借阅记录不存在", 404)
    if borrow.borrower_id != user.id:
        raise BizError("只能归还自己借到的图书", 403)
    if borrow.status != BorrowStatus.APPROVED:
        raise BizError("该借阅不在借阅中，无法申请归还")
    pending = db.scalar(
        select(ReturnRequest.id).where(
            ReturnRequest.borrow_id == borrow.id, ReturnRequest.status == ReturnStatus.PENDING
        )
    )
    if pending is not None:
        raise BizError("已有待处理的归还申请，请等待发布人确认")
    ret = ReturnRequest(
        borrow_id=borrow.id,
        book_id=borrow.book_id,
        borrower_id=user.id,
        owner_id=borrow.owner_id,
        message=data.message,
    )
    db.add(ret)
    db.commit()
    db.refresh(ret)
    return ret


def _get_return_as_owner(db: Session, user: User, return_id: int) -> ReturnRequest:
    ret = db.get(ReturnRequest, return_id)
    if ret is None:
        raise BizError("归还申请不存在", 404)
    if ret.owner_id != user.id:
        raise BizError("无权处理他人图书的归还申请", 403)
    return ret


def confirm_return(db: Session, user: User, return_id: int) -> ReturnRequest:
    ret = _get_return_as_owner(db, user, return_id)
    if not _transition(db, ReturnRequest, ret.id, ReturnStatus.PENDING, ReturnStatus.CONFIRMED):
        raise BizError("该归还申请已处理，请刷新后查看")
    # 借阅记录的 handled_at 保留为同意借出的时间，归还时间看归还申请的 handled_at
    _transition(db, BorrowRequest, ret.borrow_id, BorrowStatus.APPROVED, BorrowStatus.RETURNED, stamp=False)
    db.execute(
        update(Book)
        .where(Book.id == ret.book_id, Book.status == BookStatus.BORROWED)
        .values(status=BookStatus.AVAILABLE)
    )
    db.commit()
    db.refresh(ret)
    return ret


def reject_return(db: Session, user: User, return_id: int) -> ReturnRequest:
    ret = _get_return_as_owner(db, user, return_id)
    if not _transition(db, ReturnRequest, ret.id, ReturnStatus.PENDING, ReturnStatus.REJECTED):
        raise BizError("该归还申请已处理，请刷新后查看")
    db.commit()
    db.refresh(ret)
    return ret


def list_returns(
    db: Session,
    page: int,
    size: int,
    status: str | None = None,
    borrower_id: int | None = None,
    owner_id: int | None = None,
) -> dict:
    conditions = []
    if status:
        conditions.append(ReturnRequest.status == status)
    if borrower_id is not None:
        conditions.append(ReturnRequest.borrower_id == borrower_id)
    if owner_id is not None:
        conditions.append(ReturnRequest.owner_id == owner_id)
    return paginate(db, ReturnRequest, conditions, [ReturnRequest.id.desc()], page, size)
